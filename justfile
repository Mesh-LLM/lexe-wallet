build:
    cargo build --release --locked
check:
    cargo fmt --all --check
    cargo check --locked --all-targets
    cargo clippy --locked --all-targets -- -D warnings
test:
    cargo test --locked
clean:
    cargo clean
package: build
    python3 scripts/package.py
verify-package target:
    python3 scripts/release.py --verify {{target}}
