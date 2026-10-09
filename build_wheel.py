"""Build the original package as a wheel using only installed Python stdlib.

Run only during separately admitted offline packaging. No dependency resolver,
index, build backend or network is involved. Output must be a new file.
"""
import base64
import csv
import hashlib
import io
from pathlib import Path
import sys
import zipfile


def build(destination):
    root = Path(__file__).resolve().parent
    dist = 'lexical_retrieval_bench-0.1.0.dist-info'
    entries = {}
    for path in sorted((root / 'lexical_retrieval_bench').glob('*.py')):
        entries['lexical_retrieval_bench/' + path.name] = path.read_bytes()
    entries[dist + '/METADATA'] = (b'Metadata-Version: 2.1\nName: lexical-retrieval-bench\nVersion: 0.1.0\n'
                                  b'Summary: Original dependency-free lexical retrieval benchmark\nRequires-Python: >=3.10\n\n')
    entries[dist + '/WHEEL'] = b'Wheel-Version: 1.0\nGenerator: original-stdlib-builder\nRoot-Is-Purelib: true\nTag: py3-none-any\n'
    record = io.StringIO(newline='')
    writer = csv.writer(record, lineterminator='\n')
    for name, raw in sorted(entries.items()):
        encoded = base64.urlsafe_b64encode(hashlib.sha256(raw).digest()).rstrip(b'=').decode('ascii')
        writer.writerow((name, 'sha256=' + encoded, len(raw)))
    writer.writerow((dist + '/RECORD', '', ''))
    entries[dist + '/RECORD'] = record.getvalue().encode()
    with zipfile.ZipFile(destination, 'x', compression=zipfile.ZIP_STORED) as archive:
        for name, raw in sorted(entries.items()):
            item = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            item.external_attr = 0o100644 << 16
            archive.writestr(item, raw)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('usage: python build_wheel.py NEW_WHEEL_PATH')
    build(sys.argv[1])
