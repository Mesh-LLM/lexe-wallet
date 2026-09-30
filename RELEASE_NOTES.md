Standalone Lexe wallet provider for Mesh's `wallet.v1` capability. Install with:

```sh
mesh-llm plugins install Mesh-LLM/lexe-wallet
```

Use a Mesh host with payments enabled and built-in Lexe disabled. This release
is for fresh/unpinned profiles. Existing `wallet-lexe` pins require a separate
identity-checked adoption procedure; do not delete wallet pins or recovery seeds.
Installation does not authorize spending. Mesh retains policy, budgets and ledger.

Native archives and SHA-256 sidecars cover macOS Apple Silicon/Intel, Linux
ARM64/x86_64 and Windows ARM64/x86_64. macOS requires 13.3 or later; Linux
x86_64 builds on Ubuntu 22.04 and ARM64 on Ubuntu 24.04. Windows uses MSVC.
Artifacts are not notarized or Authenticode-signed. Build/test coverage is not a
claim of live settlement qualification on every platform. Live paid inference
was verified between two Apple Silicon Macs with the external wallet provider.
