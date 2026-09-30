# Lexe wallet for mesh-llm (draft)

Standalone `wallet.v1` plugin, with a reusable `mesh-wallet-lexe` library for
future opt-in build-time embedding. Mesh retains budgets, ledger and recovery.

## Intended installation after GitHub release publication

```sh
mesh-llm plugins install Mesh-LLM/lexe-wallet
```

Restart your normal mesh node. Installed, enabled plugins are discovered by the
host. Use a mesh build with payments enabled and built-in Lexe disabled (PR
#2121). No manual command path is needed. This repository is currently a draft:
there is no published GitHub release to install yet.

The host supplies `MESH_LLM_PLUGIN_NAME`, `MESH_LLM_PLUGIN_ENDPOINT` and transport.
The plugin advertises `wallet.v1`, not MCP payment tools. Installation/startup
does not provision a wallet: the first host `wallet_open` request does.

## Development

Use `just check`, `just test`, `just build`, and `just package`. Shared protocol
crates are pinned to mesh source commit `51fd00a99806afa1bc1db0abbedc5d0702c9900b`.
The Lexe SDK remains pinned to 0.1.24. `just package` packages the native host
platform only; other targets must be built and validated on their platforms.
No release automation or cross-platform qualification is claimed yet.

Local archive installation for an isolated test profile:

```sh
mesh-llm plugins install --name lexe-wallet --version 0.1.0 --archive dist/lexe-wallet-v0.1.0-<target>.tar.gz
```

Consult `mesh-llm plugins install --help` for local name options for your version.
Never run a smoke test against an existing funded profile. Automated tests use
synthetic data and must not provision wallets or move money. Live money tests
require separate authorization. Run `just clean` when verification is finished.

## State and safety

The host supplies the wallet directory. Existing wallet migration is NOT in
scope: do not delete or rewrite a provider pin to bypass identity checking.
**Existing wallets pinned to `wallet-lexe` will not open with `lexe-wallet`.**
Installing this plugin and restarting is not an upgrade path for those profiles:
the host safely refuses the changed provider name, even though the seed and data
format are unchanged. Fresh profiles are the draft's target. Safe, identity-checked
pin adoption remains a follow-up; before a first release, either implement and
validate it or explicitly qualify that release for fresh/unpinned profiles only.
The backend retains its directory lock and protects its plaintext recovery seed
with Unix permissions. Back up that seed securely; do not put it in plugin
packages, logs or repositories. Windows permissions need platform validation.
Plugin removal must not remove host wallet state.

After a possibly submitted payment, errors remain uncertain and recovery uses
the payment hash; never blindly retry a send. A plugin process is trusted local
code, not a sandbox. Do not enable two wallet providers for the same profile.

## Provenance

Backend and watcher extracted from Mesh-LLM/mesh-llm at
`2129f4bb19862dfb425d27eaf9230cae90dbb850`, under `crates/mesh-wallet-lexe`.
The dependency baseline is `51fd00a99806afa1bc1db0abbedc5d0702c9900b`;
the extracted backend and shared contract sources are unchanged between these
commits. The extraction revision records where the files were copied from, not a
second protocol version. Shared contract implementation is a dependency, not a
copied fork. Git dependencies require fetching the mesh repository; registry
publication of this crate is not currently supported.

The copied LICENSE contains Apache-2.0; upstream Cargo metadata declares
`MIT OR Apache-2.0`. That inherited licensing discrepancy needs resolution before
publication; this draft does not supply a missing MIT grant.

### Automated integration evidence

On Unix, the full suite builds an archive containing the real plugin executable,
installs it with mesh's `install_plugin_archive` into a temporary store, then
launches the installed executable using a protocol host fixture. It verifies
`wallet.v1` negotiation, no advertised MCP payment tools or HTTP bindings,
structured `not_open` before opening a wallet, forced process death/restart and
clean shutdown. This is real installer/process/IPC evidence, not a full mesh-node
or paid-inference test. It never sends `wallet_open` or contacts Lexe services.
Consequently it does not prove wallet-open behavior, cross-process directory
locking, the host's `PluginWalletFactory` lifecycle, post-submission recovery,
missing/disabled provider handling, or Windows packaging/transport. The startup
filesystem assertion only checks the temporary HOME; it is not evidence about
writes to a host-supplied wallet directory. Contract compatibility with newer host
revisions still requires explicit validation.

The extracted backend retains the current Lexe data format and host-provided
`payments/lexe` location, including `seedphrase.txt`. Optional adoption of old host
provider pins is a separate follow-up, not a reason to change recovery material.
