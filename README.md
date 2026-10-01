# Note: still work in progress, not usable yet. 

# Lexe wallet for mesh-llm

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
The on-demand release workflow builds and tests native macOS, Linux and Windows
archives. See [RELEASING.md](RELEASING.md) for dispatch and manual instructions.
Native build coverage does not imply live wallet qualification on each platform.

Local archive installation for an isolated test profile:

```sh
mesh-llm plugins install --name lexe-wallet --version 0.1.0 --archive dist/lexe-wallet-v0.1.0-<target>.tar.gz
```

Consult `mesh-llm plugins install --help` for local name options for your version.
Never run a smoke test against an existing funded profile. Automated tests use
synthetic data and must not provision wallets or move money. Live money tests
require separate authorization. Run `just clean` when verification is finished.

## State and safety

The host supplies the wallet directory (`payments/wallets/lexe-wallet/`). Do not
delete or hand-edit a provider pin to get around the identity check.
Profiles pinned to the former built-in `wallet-lexe` will not open with
`lexe-wallet`; the host refuses the changed provider name.
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

The extracted code is distributed under Apache-2.0, selecting the Apache-2.0
option from upstream’s `MIT OR Apache-2.0` declaration. The upstream Apache
LICENSE is retained unchanged; this repository does not claim a missing MIT grant.

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

The extracted backend retains the current Lexe data format, including
`seedphrase.txt`. Hosts with mesh-llm#2133 give each wallet plugin its own
directory, so this plugin runs in `payments/wallets/lexe-wallet/` (older hosts
used `payments/lexe/`). To keep a funded test wallet, copy `seedphrase.txt` into
the new directory before first start and run `mesh-llm wallet unpin` if the
ledger is pinned to the old name. Optional adoption of old host
provider pins is a separate follow-up, not a reason to change recovery material.
