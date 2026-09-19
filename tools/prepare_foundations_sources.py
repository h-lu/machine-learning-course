"""Materialize reviewed UTF-8 source edits on one feature branch; execute no course code."""
from __future__ import annotations

import hashlib
import json
import lzma
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys

BASE = '3887169ed3f28990f2b9d2246db78c9c2b2803f6'
BRANCH = 'refs/heads/course/foundations-s01-s06'
PACKED_SHA = '7533005ba675066d6ab03031693069a5764c2b7d4bfd26ab7089eaf9a0ec2e9d'
PACKED_BYTES = 70952
JSON_BYTES = 366987
COUNT = 95


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def blob(data: bytes) -> str:
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()


def main() -> None:
    verify_only = sys.argv[1:] == ['--verify-only']
    require(verify_only or not sys.argv[1:], 'Unsupported arguments')
    if not verify_only:
        require(os.getenv('GITHUB_REPOSITORY') == 'h-lu/machine-learning-course', 'Wrong repository')
        require(os.getenv('GITHUB_REF') == BRANCH, 'Wrong feature branch')
        require(subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip() == os.getenv('GITHUB_SHA'), 'Checkout moved')
    root = Path(subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], text=True).strip()).resolve()
    os.chdir(root)
    require(not subprocess.check_output(['git', 'status', '--porcelain', '--untracked-files=no']), 'Tracked worktree is not clean')
    parts = root / '.github/foundations-transfer'
    packed = b''.join((parts / f'part-{i:02d}.xzpart').read_bytes() for i in range(1, 9))
    require(len(packed) == PACKED_BYTES and hashlib.sha256(packed).hexdigest() == PACKED_SHA, 'Transfer checksum mismatch')
    decoder = lzma.LZMADecompressor(memlimit=512 * 1024 * 1024)
    raw = decoder.decompress(packed, max_length=JSON_BYTES + 1)
    require(decoder.eof and not decoder.unused_data and len(raw) == JSON_BYTES, 'Invalid compressed source')
    spec = json.loads(raw.decode('utf-8'))
    require(spec['base_commit'] == BASE and len(spec['files']) == COUNT, 'Wrong source manifest')
    outputs = []
    paths = []
    for entry in spec['files']:
        name = entry['path']
        path = PurePosixPath(name)
        require(isinstance(name, str) and not path.is_absolute() and '..' not in path.parts and str(path) == name, 'Unsafe path')
        require(name == 'AGENTS.md' or path.parts[0] in {'course-student-template', 'course-instructor', 'machine-learning-course', 'ml-check', 'tools'}, 'Unexpected source location')
        require('.github' not in path.parts and '.git' not in path.parts and path.suffix in {'.py', '.md', '.json'}, 'Unexpected file type')
        target = root / name
        require(target.resolve().is_relative_to(root), 'Path leaves repository')
        require(not any(p.is_symlink() for p in [target, *target.parents]), 'Symlink is not permitted')
        if entry['old_sha'] is None:
            require(not target.exists(), 'New file already exists: ' + name)
            old = b''
        else:
            require(target.is_file(), 'Missing original: ' + name)
            old = target.read_bytes()
            require(blob(old) == entry['old_sha'], 'Original changed: ' + name)
        end_before = 0
        for start, end, text in entry['edits']:
            require(type(start) is int and type(end) is int and isinstance(text, str), 'Invalid edit')
            require(end_before <= start <= end <= len(old), 'Overlapping edits')
            end_before = end
        new = old
        for start, end, text in reversed(entry['edits']):
            new = new[:start] + text.encode('utf-8') + new[end:]
        require(blob(new) == entry['new_sha'], 'Replacement checksum mismatch: ' + name)
        new.decode('utf-8')
        paths.append(name)
        outputs.append((target, new))
    require(len(paths) == len(set(paths)) == COUNT, 'Duplicate source paths')
    if verify_only:
        print(f'Verified {COUNT} exact source replacements; wrote no files.')
        return
    # Validate every source before writing any; no imports or execution of course code.
    for target, data in outputs:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    subprocess.run(['git', 'add', '--', *paths], check=True)
    staged = subprocess.check_output(['git', 'diff', '--cached', '--name-only', '-z']).decode().rstrip('\0').split('\0')
    require(set(staged) == set(paths), 'Unexpected staged change')
    subprocess.run(['git', 'diff', '--cached', '--check'], check=True)
    print(f'Materialized and staged {COUNT} verified source files; no course code executed.')


if __name__ == '__main__':
    main()
