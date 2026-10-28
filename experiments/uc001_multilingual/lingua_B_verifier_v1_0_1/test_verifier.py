import io
import json
from pathlib import Path
import sys
import time
import unittest
import zipfile

from verify_retained import ORIGINAL, VerificationError, verify_declared_licenses, verify_retained


DIAGNOSTICS = {}


class LicenseRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.metadata = (ORIGINAL / 'publisher-wheel.METADATA').read_bytes()
        cls.license = (ORIGINAL / 'publisher-LICENSE.txt').read_bytes()
        cls.dist_info = 'lingua_language_detector-2.2.0.dist-info'
        cls.metadata_member = cls.dist_info + '/METADATA'
        cls.license_member = cls.dist_info + '/licenses/LICENSE'

    def fixture(self, license_content=None, decoy=False):
        data = io.BytesIO()
        with zipfile.ZipFile(data, 'w') as archive:
            archive.writestr(self.metadata_member, self.metadata)
            if license_content is not None:
                archive.writestr(self.license_member, license_content)
            if decoy:
                archive.writestr(self.dist_info + '/LICENSE.txt', self.license)
        data.seek(0)
        return zipfile.ZipFile(data)

    def test_retained_wheel_declared_license_is_exact(self):
        result = verify_retained()
        self.assertEqual(result['version'], '1.0.1')
        self.assertEqual(result['licenses'][0]['archive_member'], self.license_member)
        self.assertEqual(result['licenses'][0]['declared'], 'LICENSE')
        self.assertEqual(result['licenses'][0]['bytes'], 11357)
        self.assertTrue(result['licenses'][0]['exact_content_match'])
        self.assertEqual(result['licenses'][0]['sha256'],
                         'c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4')
        self.assertEqual(result['wheel_sha256'],
                         '63d99c7570ba09525f1702e4e4b2362f8f1f7e0a0fba93a3a53d3f322e00659d')
        DIAGNOSTICS[self.id()] = result

    def test_missing_license_rejected(self):
        with self.fixture() as archive:
            with self.assertRaisesRegex(VerificationError, 'Missing declared license content: .*licenses/LICENSE') as caught:
                verify_declared_licenses(archive, self.metadata_member, self.metadata,
                                         {'LICENSE': self.license})
        DIAGNOSTICS[self.id()] = str(caught.exception)

    def test_altered_license_rejected(self):
        altered = self.license.replace(b'Apache License', b'Altered License', 1)
        self.assertNotEqual(altered, self.license)
        with self.fixture(license_content=altered) as archive:
            with self.assertRaisesRegex(VerificationError, 'License content mismatch: .*licenses/LICENSE') as caught:
                verify_declared_licenses(archive, self.metadata_member, self.metadata,
                                         {'LICENSE': self.license})
        DIAGNOSTICS[self.id()] = str(caught.exception)

    def test_mislocated_matching_decoy_is_not_accepted(self):
        with self.fixture(decoy=True) as archive:
            with self.assertRaisesRegex(VerificationError, 'Missing declared license content') as caught:
                verify_declared_licenses(archive, self.metadata_member, self.metadata,
                                         {'LICENSE': self.license})
        DIAGNOSTICS[self.id()] = str(caught.exception)


def prohibit_execution(event, args):
    if event.startswith('socket.') or event in {'subprocess.Popen', 'os.system'}:
        raise RuntimeError('Offline verification forbids network/process execution: ' + event)
    if event == 'import' and (args[0] == 'lingua' or args[0].startswith('lingua.')):
        raise RuntimeError('Offline verification forbids importing Lingua')


if __name__ == '__main__':
    sys.addaudithook(prohibit_execution)
    started = time.monotonic()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(LicenseRegression)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = {'tests_run': result.testsRun, 'failures': len(result.failures),
              'errors': len(result.errors), 'passed': result.wasSuccessful(),
              'seconds': time.monotonic() - started, 'diagnostics': DIAGNOSTICS,
              'lingua_imported': 'lingua' in sys.modules,
              'scope': 'Read-only retained wheel and in-memory synthetic ZIP fixtures; no install, network, process start or detector call.'}
    path = Path(__file__).with_name('regressions.json')
    with path.open('x') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    sys.exit(0 if result.wasSuccessful() else 1)
