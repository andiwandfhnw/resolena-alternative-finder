from pathlib import Path
import base64
import email
import hashlib
import json
import os
import time
import urllib.request
import zipfile

from supervise import RUN, append, write


pin = json.loads((RUN / 'artifact-pin.json').read_text())
attempt = json.loads((RUN / 'attempt.json').read_text())
ledger = json.loads((RUN / 'acquisition.json').read_text())
wheel = pin['wheel']
target = RUN / wheel['filename']
partial = target.with_suffix('.whl.partial')
assert not target.exists() and not partial.exists(), 'No repeated acquisition'
assert sum(x['bytes'] for x in ledger) + wheel['size'] <= 200000000
got = 0
digest = hashlib.sha256()
with urllib.request.urlopen(wheel['url'], timeout=30) as response, partial.open('xb') as output:
    assert response.url.startswith('https://files.pythonhosted.org/')
    assert int(response.headers['Content-Length']) == wheel['size']
    while True:
        if time.monotonic() >= attempt['deadline_monotonic']:
            raise RuntimeError('deadline during acquisition')
        block = response.read(1024 * 1024)
        if not block:
            break
        got += len(block)
        assert got <= wheel['size'] and sum(x['bytes'] for x in ledger) + got <= 200000000
        output.write(block)
        digest.update(block)
        write(RUN / 'download-progress.json', {'bytes': got, 'sha256_so_far': digest.hexdigest(), 'monotonic': time.monotonic()})
    output.flush()
    os.fsync(output.fileno())
assert got == wheel['size'] and digest.hexdigest() == wheel['sha256']
partial.rename(target)
ledger.append({'kind': 'wheel', 'url': wheel['url'], 'path': wheel['filename'],
               'bytes': got, 'sha256': digest.hexdigest()})
write(RUN / 'acquisition.json', ledger)
with zipfile.ZipFile(target) as z:
    assert z.testzip() is None
    assert all(not x.startswith('/') and '..' not in Path(x).parts for x in z.namelist())
    installed_upper_bytes = sum(x.file_size for x in z.infolist())
    assert installed_upper_bytes + target.stat().st_size + 10000000 < 1024 ** 3, 'Wheel expansion would exceed scratch allowance'
    md_name = next(n for n in z.namelist() if n.endswith('.dist-info/METADATA'))
    md = z.read(md_name)
    assert md == (RUN / 'publisher-wheel.METADATA').read_bytes()
    license_name = next(n for n in z.namelist() if n.endswith('/LICENSE.txt'))
    license_bytes = z.read(license_name)
    assert license_bytes == (RUN / 'publisher-LICENSE.txt').read_bytes()
    wheel_record = next(n for n in z.namelist() if n.endswith('.dist-info/WHEEL'))
    tags = z.read(wheel_record).decode()
    assert 'cp312-cp312-manylinux_2_17_x86_64' in tags
    write(RUN / 'wheel-verification.json', {'sha256': digest.hexdigest(), 'size': got,
          'metadata_sha256': hashlib.sha256(md).hexdigest(), 'metadata_matches_publisher': True,
          'license_sha256': hashlib.sha256(license_bytes).hexdigest(), 'license_matches_publisher': True,
          'license': 'Apache-2.0', 'wheel_tags': tags, 'active_dependencies': [],
          'uncompressed_wheel_bytes': installed_upper_bytes,
          'excluded_test_extra': "pytest==9.0.1 ; extra == 'test'"})
print(json.dumps({'acquired_total_bytes': sum(x['bytes'] for x in ledger), 'wheel_verified': True}))
