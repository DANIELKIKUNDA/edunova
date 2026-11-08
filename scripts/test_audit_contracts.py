"""Negative controls for the historical audit's version boundary."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from historical_audit_contracts import release_at_least


class ReleaseBoundaryTests(unittest.TestCase):
    def test_numeric_versions_and_build_numbers(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            pub = root / 'apps/mobile/pubspec.yaml'
            pub.parent.mkdir(parents=True)
            for actual, minimum, expected in [
                ('0.53.0+18000', '0.11.1+15', True),
                ('0.9.0+999', '0.11.1+15', False),
                ('0.11.1+14', '0.11.1+15', False),
                ('0.11.1+15', '0.11.1+15', True),
                ('garbage', '0.11.1', False),
            ]:
                with self.subTest(actual=actual):
                    pub.write_text(f'version: {actual}\n', encoding='utf8')
                    self.assertEqual(release_at_least(root, 'mobile', minimum), expected)

    def test_api_metadata_must_use_canonical_version(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            app = root / 'services/api/app'
            app.mkdir(parents=True)
            (app/'version.py').write_text('__version__ = "0.52.7"', encoding='utf8')
            main = app/'main.py'
            valid = 'from app.version import __version__\nversion=__version__\nhealth={"version": __version__}\n'
            main.write_text(valid, encoding='utf8')
            self.assertTrue(release_at_least(root, 'api', '0.27.2'))
            self.assertFalse(release_at_least(root, 'api', '0.53.0'))
            main.write_text(valid.replace('version=__version__', 'version="0.27.2"'), encoding='utf8')
            self.assertFalse(release_at_least(root, 'api', '0.27.2'))


if __name__ == '__main__':
    unittest.main()
