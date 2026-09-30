"""Offline release-contract tests; no build, network or wallet operations."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('release', Path(__file__).with_name('release.py'))
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


class ReleaseTests(unittest.TestCase):
    def test_versions_must_match(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / 'Cargo.toml').write_text('[package]\nversion="0.1.0"\n')
            (root / 'plugin.toml').write_text('version="0.2.0"\n')
            with self.assertRaises(ValueError):
                release.version(root)

    def test_missing_platform_blocks_publication(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / 'Cargo.toml').write_text('[package]\nversion="0.1.0"\n')
            (root / 'plugin.toml').write_text('version="0.1.0"\n')
            with self.assertRaises(FileNotFoundError):
                release.verify(root, release.TARGETS)

    def test_existing_mac_archive(self):
        root = Path(__file__).resolve().parents[1]
        if not (root / 'dist/lexe-wallet-v0.1.0-aarch64-apple-darwin.tar.gz').exists():
            self.skipTest('local archive not built')
        self.assertEqual(len(release.verify(root, ['aarch64-apple-darwin'])), 2)


if __name__ == '__main__':
    unittest.main()
