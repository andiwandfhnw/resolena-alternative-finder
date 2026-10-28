import email
import hashlib
import json
from pathlib import Path, PurePosixPath
import platform
import sys
import zipfile


VERSION = '1.0.1'
ORIGINAL = Path(__file__).resolve().parent.parent / 'lingua_B_2026_10_15'
RETAINED = ORIGINAL.parents[2] / 'build/lingua-b-20261015'
ORIGINAL_FREEZE_SHA256 = '20c23e875547f114d57298c60b6c1e6fa8ee304bfd3347298228e9e815661194'


class VerificationError(ValueError):
    pass


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def require(condition, message):
    if not condition:
        raise VerificationError(message)


def verify_declared_licenses(archive, metadata_member, metadata, expected_contents):
    declared = email.message_from_bytes(metadata).get_all('License-File', [])
    require(bool(declared), 'Missing License-File declaration in wheel METADATA')
    require(len(set(declared)) == len(declared), 'Duplicate License-File declaration')
    info_dir = PurePosixPath(metadata_member).parent
    require(info_dir.name.endswith('.dist-info'), 'Invalid wheel metadata directory')
    verified = []
    for name in declared:
        relative = PurePosixPath(name)
        require(bool(name) and not relative.is_absolute() and '..' not in relative.parts
                and '\\' not in name and str(relative) == name and name != '.',
                'Unsafe declared license path: ' + name)
        require(name in expected_contents, 'No pinned license content for declaration: ' + name)
        member = str(info_dir / 'licenses' / relative)
        count = archive.namelist().count(member)
        require(count != 0, 'Missing declared license content: ' + member + ' (License-File: ' + name + ')')
        require(count == 1, 'Duplicate declared license member: ' + member)
        actual = archive.read(member)
        expected = expected_contents[name]
        require(actual == expected, 'License content mismatch: ' + member +
                '; expected SHA-256 ' + hashlib.sha256(expected).hexdigest() +
                ', actual SHA-256 ' + hashlib.sha256(actual).hexdigest())
        verified.append({'declared': name, 'archive_member': member,
                         'bytes': len(actual), 'sha256': hashlib.sha256(actual).hexdigest(),
                         'exact_content_match': True})
    require(set(declared) == set(expected_contents), 'Declared licenses do not match pinned license references')
    return verified


def verify_retained():
    require(sha256(ORIGINAL / 'freeze.json') == ORIGINAL_FREEZE_SHA256, 'Original freeze checksum mismatch')
    freeze = json.loads((ORIGINAL / 'freeze.json').read_text())
    for name in ['artifact-pin.json', 'publisher-wheel.METADATA', 'publisher-LICENSE.txt', 'config.json']:
        require(sha256(ORIGINAL / name) == freeze['files'][name], 'Pinned input checksum mismatch: ' + name)
    pin = json.loads((ORIGINAL / 'artifact-pin.json').read_text())
    config = json.loads((ORIGINAL / 'config.json').read_text())
    wheel = RETAINED / pin['wheel']['filename']
    require(wheel.is_file(), 'Retained wheel is missing: ' + str(wheel))
    require(wheel.stat().st_size == pin['wheel']['size'], 'Retained wheel size mismatch')
    digest = sha256(wheel)
    require(digest == pin['wheel']['sha256'], 'Retained wheel checksum mismatch')
    require(pin['planned_total_acquisition_bytes'] <= config['limits']['acquisition_bytes'],
            'Previously recorded acquisition exceeds unchanged cap')
    require(sys.implementation.name == 'cpython' and sys.version_info[:2] == (3, 12)
            and sys.platform == 'linux' and platform.machine() == 'x86_64',
            'Pinned wheel requires existing CPython 3.12 / Linux x86-64; no upgrade or fallback')
    libc, version = platform.libc_ver()
    require(libc == 'glibc' and tuple(int(v) for v in version.split('.')[:2]) >= (2, 17),
            'Pinned wheel requires glibc >=2.17')
    with zipfile.ZipFile(wheel) as archive:
        require(archive.testzip() is None, 'Wheel ZIP CRC failure')
        names = archive.namelist()
        require(all(not PurePosixPath(n).is_absolute() and '..' not in PurePosixPath(n).parts
                    and '\\' not in n for n in names), 'Unsafe wheel member path')
        require(len(names) == len(set(names)), 'Duplicate wheel archive member')
        installed_upper = sum(i.file_size for i in archive.infolist())
        require(installed_upper + wheel.stat().st_size + 10000000 < config['limits']['additional_scratch_bytes'],
                'Wheel expansion would exceed unchanged scratch allowance')
        metadata_members = [n for n in names if n.endswith('.dist-info/METADATA')]
        require(len(metadata_members) == 1, 'Expected exactly one wheel METADATA member')
        metadata_member = metadata_members[0]
        metadata = archive.read(metadata_member)
        require(metadata == (ORIGINAL / 'publisher-wheel.METADATA').read_bytes(), 'Publisher METADATA content mismatch')
        message = email.message_from_bytes(metadata)
        require(message.get_all('Requires-Dist', []) == pin['requires_dist'], 'Dependency metadata mismatch')
        require(pin['active_dependencies'] == [] and pin['requires_dist'] == ["pytest==9.0.1 ; extra == 'test'"],
                'Unexpected active Python dependency; no installation or acquisition permitted')
        licenses = verify_declared_licenses(archive, metadata_member, metadata,
                                            {'LICENSE': (ORIGINAL / 'publisher-LICENSE.txt').read_bytes()})
        wheel_records = [n for n in names if n.endswith('.dist-info/WHEEL')]
        require(len(wheel_records) == 1, 'Expected exactly one WHEEL tag record')
        tags = archive.read(wheel_records[0]).decode()
        require('Tag: cp312-cp312-manylinux_2_17_x86_64' in tags, 'Pinned compatible wheel tag missing')
    return {'version': VERSION, 'wheel': str(wheel), 'wheel_sha256': digest,
            'wheel_bytes': wheel.stat().st_size, 'uncompressed_wheel_bytes': installed_upper,
            'metadata_sha256': hashlib.sha256(metadata).hexdigest(),
            'metadata_matches_publisher': True, 'licenses': licenses,
            'active_python_dependencies': [], 'unchanged_limits': config['limits'],
            'new_acquisition_bytes': 0, 'installation_performed': False,
            'lingua_imported': False, 'detector_calls': 0,
            'scope': 'Offline retained-artifact verification only; native loading and detector behaviour untested.'}


if __name__ == '__main__':
    try:
        print(json.dumps(verify_retained(), indent=2))
    except (VerificationError, OSError, zipfile.BadZipFile) as error:
        print('Verification failed: ' + str(error), file=sys.stderr)
        sys.exit(1)
