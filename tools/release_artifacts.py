"""Release-only verification of built files against an immutable Git commit."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tarfile
import zipfile

TAG = 'v0.1.0-alpha.1'
COMMIT = '70d43abb5bbc5350e7df2ed20e41847bba36938e'
RELEASE_ID = 407852654
WHEEL = 'linux_opsec_auditor-0.1.0a1-py3-none-any.whl'
SOURCE = 'linux_opsec_auditor-0.1.0a1.tar.gz'
ASSETS = {WHEEL, SOURCE, 'SHA256SUMS'}


class VerificationError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise VerificationError(message)


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args], stderr=subprocess.DEVNULL)


def checksums(directory):
    directory = Path(directory)
    content = ''.join(f'{hashlib.sha256((directory/name).read_bytes()).hexdigest()}  {name}\n'
                      for name in sorted({WHEEL, SOURCE}))
    (directory/'SHA256SUMS').write_text(content)


def verify(directory, repo, expected_commit=COMMIT, tag=TAG):
    directory, repo = Path(directory), Path(repo)
    require(git(repo, 'rev-parse', f'{tag}^{{commit}}').decode().strip() == expected_commit, 'tag does not match expected commit')
    parsed = {}
    for line in (directory/'SHA256SUMS').read_text().splitlines():
        match = re.fullmatch(r'([a-f0-9]{64})  ([A-Za-z0-9_.-]+)', line)
        require(match is not None, 'invalid checksum entry')
        digest, name = match.groups()
        require(name not in parsed, 'duplicate checksum entry')
        parsed[name] = digest
    require(set(parsed) == {WHEEL, SOURCE}, 'unexpected checksum coverage')
    for name, digest in parsed.items():
        require(hashlib.sha256((directory/name).read_bytes()).hexdigest() == digest, 'checksum mismatch')
    paths = git(repo, 'ls-tree', '-r', '--name-only', expected_commit).decode().splitlines()
    package = [p for p in paths if p.startswith('src/linux_opsec_auditor/')]
    require(bool(package), 'no package files at expected commit')
    with zipfile.ZipFile(directory/WHEEL) as wheel:
        names = wheel.namelist()
        require(len(names) == len(set(names)), 'duplicate wheel file')
        for p in package:
            require(wheel.read(p[4:]) == git(repo, 'show', f'{expected_commit}:{p}'), 'wheel source differs from expected commit')
        prefix = 'linux_opsec_auditor-0.1.0a1.dist-info/'
        allowed = {p[4:] for p in package}
        allowed.update(prefix+p for p in ['METADATA', 'WHEEL', 'RECORD', 'entry_points.txt', 'top_level.txt', 'licenses/LICENSE'])
        require(set(names) <= allowed, 'unexpected wheel payload')
        metadata = wheel.read(prefix+'METADATA').decode()
        require('\nVersion: 0.1.0a1\n' in metadata, 'incorrect wheel version')
        require('\nRequires-Python: >=3.12\n' in metadata, 'incorrect Python requirement')
        require('\nRequires-Dist:' not in metadata, 'unexpected runtime dependency')
    with tarfile.open(directory/SOURCE) as archive:
        members = archive.getmembers()
        names = [m.name for m in members]
        require(len(names) == len(set(names)), 'duplicate source member')
        for member in members:
            require(not member.name.startswith('/') and '..' not in member.name.split('/'), 'unsafe source archive path')
            require(member.isdir() or member.isfile(), 'nonregular source archive member')
        for p in paths:
            if p == '.gitignore':
                continue
            member = archive.getmember('linux_opsec_auditor-0.1.0a1/'+p)
            require(member.size <= 1_048_576, 'oversized source member')
            require(archive.extractfile(member).read() == git(repo, 'show', f'{expected_commit}:{p}'), 'source archive differs from expected commit')
    print('Release artifacts verified: exact tagged source, metadata and two SHA256 checksums.')
    return parsed


def verify_release_metadata(metadata, public=False, require_assets=False):
    require(metadata['id'] == RELEASE_ID, 'unexpected release ID; never create a duplicate release')
    require(metadata['tag_name'] == TAG, 'unexpected release tag')
    require(metadata['target_commitish'] == COMMIT, 'unexpected release commit')
    require(metadata['prerelease'] is True, 'release must remain a prerelease')
    if public:
        require(metadata['draft'] is False, 'release remains a draft')
    names = [a['name'] for a in metadata['assets']]
    require(len(names) == len(set(names)) and set(names) <= ASSETS, 'unexpected or duplicate release assets')
    if require_assets:
        require(set(names) == ASSETS, 'release assets incomplete')
        require(all(a['state'] == 'uploaded' and a['size'] > 0 for a in metadata['assets']), 'release asset not ready')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('command', choices=['checksums', 'verify', 'metadata'])
    p.add_argument('--directory', default='dist')
    p.add_argument('--repo', default='.')
    p.add_argument('--input')
    p.add_argument('--public', action='store_true')
    p.add_argument('--require-assets', action='store_true')
    args = p.parse_args()
    if args.command == 'checksums':
        checksums(args.directory)
    elif args.command == 'verify':
        verify(args.directory, args.repo)
    else:
        verify_release_metadata(json.loads(Path(args.input).read_text()), args.public, args.require_assets)
        print('Existing release identity and asset state verified.')


if __name__ == '__main__':
    main()
