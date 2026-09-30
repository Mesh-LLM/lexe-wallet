"""Package an already-built native executable using mesh plugin conventions."""
import hashlib
from pathlib import Path
import subprocess
import tarfile
import tomllib
import zipfile

root = Path(__file__).resolve().parents[1]
version = tomllib.loads((root / "Cargo.toml").read_text())["package"]["version"]
target = next(line.split(": ", 1)[1] for line in subprocess.check_output(
    ["rustc", "-vV"], text=True).splitlines() if line.startswith("host: "))
windows = "windows" in target
binary = "lexe-wallet.exe" if windows else "lexe-wallet"
files = [(root / "target/release" / binary, binary)] + [
    (root / name, name) for name in ("plugin.toml", "README.md", "LICENSE")]
for source, _ in files:
    if not source.is_file():
        raise SystemExit(f"Missing {source}; run just build first")
(root / "dist").mkdir(exist_ok=True)
archive = root / "dist" / f"lexe-wallet-v{version}-{target}.{'zip' if windows else 'tar.gz'}"
if windows:
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
        for source, name in files:
            bundle.write(source, f"lexe-wallet/{name}")
else:
    with tarfile.open(archive, "w:gz") as bundle:
        for source, name in files:
            bundle.add(source, arcname=f"lexe-wallet/{name}")
archive.with_name(archive.name + ".sha256").write_text(
    f"{hashlib.sha256(archive.read_bytes()).hexdigest()}  {archive.name}\n")
print(archive)
