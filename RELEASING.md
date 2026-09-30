# Publishing the native wallet

The **Release wallet** workflow runs the full Rust checks and test suite, builds
natively on six GitHub-hosted runners, packages the installer archive, verifies
its checksum/metadata/executable, and uploads artifacts. PRs build but cannot
publish. No tests provision wallets, contact live wallet services or move money.

On-demand build without publication:

```sh
gh workflow run release.yml --repo Mesh-LLM/lexe-wallet --ref <reviewed-ref> -f publish=false
```

Publish the reviewed commit:

```sh
gh workflow run release.yml --repo Mesh-LLM/lexe-wallet --ref <reviewed-ref> -f publish=true
```

Keep Cargo.toml, Cargo.lock package version and plugin.toml synchronized before
releasing. Update RELEASE_NOTES.md. The version determines the `v<version>` tag.
The publish job waits for all six builds, verifies all twelve files, creates a
draft with assets, then makes it public. Existing releases are not overwritten.
If upload/publication fails, inspect the private draft; delete that draft and
its tag explicitly before retrying. Do not delete or mutate a published release
to rerun it; increment the version instead.

Workflow dispatch is available in the UI once this workflow is on the default
branch. It can then target a reviewed branch. Do not dispatch unreviewed code
with publish=true: the final job has release-write permission.

## Manual native builds

Install Rust 1.97.0 (with rustfmt/clippy), Python 3.11+, just 1.58.0, and the
platform C/C++ toolchain: Xcode command-line tools on macOS, a C compiler/CMake
on Linux, or Visual Studio C++ build tools/CMake on Windows. Use native machines
for each target; this packager intentionally does not guess cross-build targets.

```sh
just check
just test
just package
just verify-package <native-target-triple>
just clean
```

Targets: aarch64-apple-darwin, x86_64-apple-darwin,
x86_64-unknown-linux-gnu, aarch64-unknown-linux-gnu,
x86_64-pc-windows-msvc, aarch64-pc-windows-msvc.

Collect all archives and sidecars in dist/, then `python3 scripts/release.py`
performs the same all-platform verification and publication (requires gh auth).
Archive names are `lexe-wallet-v<version>-<target>.tar.gz` (Unix) or `.zip`
(Windows), containing `lexe-wallet/plugin.toml` and the native executable.

Consumers need no Rust compiler. App integrators can install these same archives
through Mesh's plugin installer and continue using the generic wallet API. Merely
copying an executable beside an app is not plugin registration. Keep existing
wallet data outside the plugin installation directory and enable only one wallet
provider. Installation and funding never imply spending authorization.
