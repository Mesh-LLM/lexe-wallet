# Lexe wallet for mesh-llm

Standalone `wallet.v1` plugin, with a reusable `mesh-wallet-lexe` library for
future opt-in build-time embedding. Mesh retains budgets, ledger and recovery.

> [!WARNING]
> This wallet is an example under exploration. Opening it can provision a mainnet
> wallet; sending moves real money. Protect recovery material and use small amounts.

## Install the external plugin

```sh
mesh-llm plugins install Mesh-LLM/lexe-wallet
```

Restart your normal mesh node. Installed, enabled plugins are discovered by the
host. MeshLLM v0.78.0 includes the payment infrastructure and uses external
wallet plugins; Lexe wallet v0.1.0 is available in this repository's releases.
No manual executable path or built-in Lexe feature is needed. Check the release
assets for your platform; a packaged target is not proof of live-money qualification.

Choose the profile **before the first wallet operation**. An explicit
`--config /absolute/path/payer/config.toml` stores payment state in
`/absolute/path/payer/payments/`, not under a separately changed HOME. The host
supplies `payments/wallets/lexe-wallet/` to this plugin. Keep the same config path
on the node and all wallet commands. An optional explicit selection is:

```toml
[payments]
wallet = "lexe-wallet"
```

Start the node, then run wallet commands in another terminal:

```sh
CONFIG="/absolute/path/payer/config.toml" # existing, selected config
mesh-llm --config "$CONFIG" client --console 3131
```

```sh
CONFIG="/absolute/path/payer/config.toml"
mesh-llm --config "$CONFIG" wallet --port 3131 policy
mesh-llm --config "$CONFIG" wallet --port 3131 get-balance
# Only if funding is needed: create an invoice, then pay it from another wallet.
mesh-llm --config "$CONFIG" wallet --port 3131 fund-wallet --amount-sats 1000
mesh-llm --config "$CONFIG" wallet --port 3131 get-transactions --limit 20
# Optional: explicitly authorize automatic paid inference within this budget.
mesh-llm --config "$CONFIG" wallet --port 3131 policy --mode automatic --daily-budget-sats 100
# Disable new automatic inference spending again.
mesh-llm --config "$CONFIG" wallet --port 3131 policy --mode free-only
```

A fresh profile is free-only. Funding does not authorize inference spending;
`fund-wallet` only creates an invoice, and 1 sat equals 1,000 msat. The policy
persists across restarts. An explicit send separately authorizes payment:

```sh
mesh-llm --config "$CONFIG" wallet --port 3131 send 'lnbc...' --max-fee-msat 1000
# Amount-less invoices additionally require --amount-msat AMOUNT.
```

Replace the invoice only when ready to pay. Wallet-dependent commands require
the running node. `--port` is its management port, not the OpenAI port. Explicit
`--config` checks that the API is using the intended payment directory. Even
`get-balance` can provision a wallet, so read the state checks below first.

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

The host supplies the wallet directory. Do not delete or rewrite a provider pin
to bypass identity checking. **Existing wallets pinned to `wallet-lexe` will not
open with `lexe-wallet`.** Installing this plugin is not an automatic migration
for those profiles; the provider name differs even if the seed format is the same.

For an existing profile already pinned to **`lexe-wallet`**, stop that profile's
node and wallet writer, then privately back up the config and entire `payments/`
directory (ledger, SQLite sidecars, pin and wallet material). Keep the existing
pin and ledger unchanged. Use `payments/wallets/lexe-wallet/` if it already exists.
If the same external-wallet profile still stores its wallet in `payments/lexe/`,
move that whole wallet directory to the current destination only while stopped
and only if the destination does not exist. Do not merge two directories. Verify
the expected recovery files and private permissions **before** opening it.

If both paths exist, the pin is absent, or its identity/provider is unexpected,
stop and resolve the provenance. Do not use `wallet unpin` as an adoption shortcut.
A wrong or empty directory can provision a new wallet before the host compares
its identity with the pin. Restart with the same config, verify known history,
balance, policy and pending records, and stop on any mismatch rather than funding
an unexpected empty wallet. No migration tooling is implemented by this README.

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

The extracted backend retains the Lexe data format, including `seedphrase.txt`.
The current host supplies `payments/wallets/lexe-wallet/`; the historical
`payments/lexe/` path is not a default for new profiles. Directory preservation
for an already matching external-wallet pin is distinct from switching a former
built-in provider pin; neither is a reason to change recovery material.
