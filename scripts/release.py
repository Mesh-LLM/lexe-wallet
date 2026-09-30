"""Validate release assets before creating a draft, then publish atomically."""
import argparse
import hashlib
from pathlib import Path
import subprocess
import tarfile
import tomllib
import zipfile

ROOT = Path(__file__).resolve().parents[1]
TARGETS = (
    "aarch64-apple-darwin", "x86_64-apple-darwin",
    "x86_64-unknown-linux-gnu", "aarch64-unknown-linux-gnu",
    "x86_64-pc-windows-msvc", "aarch64-pc-windows-msvc",
)


def version(root):
    """Require matching package and installer metadata."""
    cargo = tomllib.loads((root / "Cargo.toml").read_text())["package"]["version"]
    plugin = tomllib.loads((root / "plugin.toml").read_text())["version"]
    if cargo != plugin or not cargo or any(c not in "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ.-" for c in cargo):
        raise ValueError("Invalid or mismatched release version")
    return cargo


def verify(root, targets):
    """Check checksums and required archive entries for every requested target."""
    v = version(root)
    assets = []
    for target in targets:
        if target not in TARGETS:
            raise ValueError("Unsupported target")
        windows = "windows" in target
        ext = "zip" if windows else "tar.gz"
        archive = root / "dist" / f"lexe-wallet-v{v}-{target}.{ext}"
        checksum = archive.with_name(archive.name + ".sha256")
        expected = f"{hashlib.sha256(archive.read_bytes()).hexdigest()}  {archive.name}"
        if checksum.read_text().strip() != expected:
            raise ValueError(f"Checksum mismatch: {archive.name}")
        binary = "lexe-wallet/lexe-wallet" + (".exe" if windows else "")
        if windows:
            with zipfile.ZipFile(archive) as bundle:
                names = bundle.namelist()
                metadata = bundle.read("lexe-wallet/plugin.toml")
        else:
            with tarfile.open(archive) as bundle:
                names = bundle.getnames()
                metadata = bundle.extractfile("lexe-wallet/plugin.toml").read()
                if not bundle.getmember(binary).mode & 0o111:
                    raise ValueError("Packaged binary is not executable")
        if binary not in names or "lexe-wallet/LICENSE" not in names:
            raise ValueError("Missing executable or license")
        if tomllib.loads(metadata.decode()) != {"name": "lexe-wallet", "version": v}:
            raise ValueError("Archive metadata mismatch")
        assets.extend([archive, checksum])
    return assets


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", choices=TARGETS)
    args = parser.parse_args()
    assets = verify(ROOT, [args.verify] if args.verify else TARGETS)
    if args.verify:
        host = subprocess.check_output(["rustc", "-vV"], text=True)
        if f"host: {args.verify}\n" not in host:
            raise ValueError("Runner is not the expected native target")
        print("Verified", args.verify)
        return
    tag = "v" + version(ROOT)
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    # Never replace published assets or silently reuse an old tag. Failed draft
    # uploads remain private for inspection; delete that draft/tag before retry.
    subprocess.run(["gh", "release", "create", tag, "--draft", "--target", sha,
                    "--title", f"Lexe wallet {tag}", "--notes-file", "RELEASE_NOTES.md",
                    *map(str, assets)], check=True, cwd=ROOT)
    subprocess.run(["gh", "release", "edit", tag, "--draft=false"], check=True, cwd=ROOT)


if __name__ == "__main__":
    main()
