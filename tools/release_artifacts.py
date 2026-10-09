"""Release-only verification; accepted versions are explicitly enumerated."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tarfile
import tomllib
import zipfile

TAG = 'v0.1.0-alpha.1'
COMMIT = '70d43abb5bbc5350e7df2ed20e41847bba36938e'
RELEASE_ID = 407852654
VERSIONS = {'v0.1.0-alpha.1': '0.1.0a1', 'v0.1.0-alpha.2': '0.1.0a2'}
WHEEL = 'linux_opsec_auditor-0.1.0a1-py3-none-any.whl'
SOURCE = 'linux_opsec_auditor-0.1.0a1.tar.gz'
ASSETS = {WHEEL, SOURCE, 'SHA256SUMS'}


class VerificationError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise VerificationError(message)


def identity(tag=TAG, commit=COMMIT, release_id=RELEASE_ID):
    require(tag in VERSIONS, 'Tag вне разрешённых версий')
    require(re.fullmatch(r'[a-f0-9]{40}', commit) is not None, 'Требуется полный commit SHA')
    require(type(release_id) is int and release_id > 0, 'Требуется существующий числовой release ID')
    version = VERSIONS[tag]
    return version, f'linux_opsec_auditor-{version}-py3-none-any.whl', f'linux_opsec_auditor-{version}.tar.gz'


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args], stderr=subprocess.DEVNULL)


def checksums(directory, tag=TAG):
    _, wheel, source = identity(tag)
    directory = Path(directory)
    content = ''.join(f'{hashlib.sha256((directory/name).read_bytes()).hexdigest()}  {name}\n' for name in sorted({wheel, source}))
    (directory/'SHA256SUMS').write_text(content)


def verify(directory, repo, expected_commit=COMMIT, tag=TAG):
    version, wheel_name, source_name = identity(tag, expected_commit)
    directory, repo = Path(directory), Path(repo)
    require(git(repo, 'rev-parse', f'{tag}^{{commit}}').decode().strip() == expected_commit, 'Tag не соответствует ожидаемому commit')
    project = tomllib.loads(git(repo, 'show', f'{expected_commit}:pyproject.toml').decode())['project']
    require(project['version'] == version and project['license'] == 'MIT', 'Несогласованная версия или лицензия проекта')
    parsed = {}
    for line in (directory/'SHA256SUMS').read_text().splitlines():
        match = re.fullmatch(r'([a-f0-9]{64})  ([A-Za-z0-9_.-]+)', line)
        require(match is not None, 'Неверная запись checksum')
        digest, name = match.groups()
        require(name not in parsed, 'Повторная запись checksum')
        parsed[name] = digest
    require(set(parsed) == {wheel_name, source_name}, 'Неверный набор checksum')
    for name, digest in parsed.items():
        require(hashlib.sha256((directory/name).read_bytes()).hexdigest() == digest, 'Checksum не совпадает')
    paths = git(repo, 'ls-tree', '-r', '--name-only', expected_commit).decode().splitlines()
    package = [p for p in paths if p.startswith('src/linux_opsec_auditor/')]
    licenses = ['LICENSE'] if version == '0.1.0a1' else ['LICENSE', 'LICENSE.ru.md']
    require(bool(package) and set(licenses) <= set(paths), 'Нет исходников или license files')
    with zipfile.ZipFile(directory/wheel_name) as wheel:
        names = wheel.namelist()
        require(len(names) == len(set(names)), 'Повторный файл wheel')
        for p in package:
            require(wheel.read(p[4:]) == git(repo, 'show', f'{expected_commit}:{p}'), 'Wheel отличается от Git-исходников')
        prefix = f'linux_opsec_auditor-{version}.dist-info/'
        allowed = {p[4:] for p in package}
        allowed.update(prefix+p for p in ['METADATA', 'WHEEL', 'RECORD', 'entry_points.txt', 'top_level.txt'])
        allowed.update(prefix+'licenses/'+p for p in licenses)
        require(set(names) <= allowed, 'Неожиданный файл в wheel')
        metadata = wheel.read(prefix+'METADATA').decode()
        require(f'\nVersion: {version}\n' in metadata, 'Неверная версия wheel')
        require('\nRequires-Python: >=3.12\n' in metadata, 'Неверное требование Python')
        require('\nRequires-Dist:' not in metadata, 'Неожиданная runtime-зависимость')
        require('\nLicense-Expression: MIT\n' in metadata, 'Нет MIT в metadata')
        for name in licenses:
            require(f'\nLicense-File: {name}\n' in metadata, 'Нет license file в metadata')
            require(wheel.read(prefix+'licenses/'+name) == git(repo, 'show', f'{expected_commit}:{name}'), 'License bytes не совпадают')
    with tarfile.open(directory/source_name) as archive:
        members = archive.getmembers()
        names = [m.name for m in members]
        require(len(names) == len(set(names)), 'Повторный файл sdist')
        prefix = f'linux_opsec_auditor-{version}/'
        expected = {prefix+p for p in paths if p != '.gitignore'}
        generated = {prefix+p for p in ['PKG-INFO', 'setup.cfg']}
        generated.update(prefix+'src/linux_opsec_auditor.egg-info/'+p for p in
                         ['PKG-INFO', 'SOURCES.txt', 'dependency_links.txt', 'entry_points.txt', 'top_level.txt'])
        for member in members:
            require(not member.name.startswith('/') and '..' not in member.name.split('/'), 'Небезопасный путь архива')
            require(member.isdir() or member.isfile(), 'Нерегулярный файл архива')
            if member.isfile():
                require(member.name in expected | generated, 'Неожиданный payload sdist')
        for p in paths:
            if p == '.gitignore':
                continue
            member = archive.getmember(prefix+p)
            require(member.size <= 1_048_576, 'Слишком большой исходный файл')
            require(archive.extractfile(member).read() == git(repo, 'show', f'{expected_commit}:{p}'), 'Sdist отличается от Git-исходников')
    print('Release artifacts проверены: точный tag/commit, metadata, license files и два SHA256.')
    return parsed


def verify_release_metadata(metadata, public=False, require_assets=False, tag=TAG, expected_commit=COMMIT, release_id=RELEASE_ID):
    _, wheel, source = identity(tag, expected_commit, release_id)
    require(metadata['id'] == release_id, 'Неожиданный release ID; не создавать дубликат')
    require(metadata['tag_name'] == tag, 'Неожиданный release tag')
    require(metadata['target_commitish'] == expected_commit, 'Неожиданный release commit')
    require(metadata['prerelease'] is True, 'Выпуск должен оставаться prerelease')
    if public:
        require(metadata['draft'] is False, 'Выпуск остаётся draft')
    names = [a['name'] for a in metadata['assets']]
    allowed = {wheel, source, 'SHA256SUMS'}
    require(len(names) == len(set(names)) and set(names) <= allowed, 'Неожиданные или повторные assets')
    if require_assets:
        require(set(names) == allowed, 'Набор assets неполон')
        require(all(a['state'] == 'uploaded' and a['size'] > 0 for a in metadata['assets']), 'Asset не готов')


def main():
    p = argparse.ArgumentParser(description='Проверка release assets без изменения tag или создания release.')
    p.add_argument('command', choices=['checksums', 'verify', 'metadata'])
    p.add_argument('--directory', default='dist')
    p.add_argument('--repo', default='.')
    p.add_argument('--input')
    p.add_argument('--tag', default=TAG)
    p.add_argument('--commit', default=COMMIT)
    p.add_argument('--release-id', type=int, default=RELEASE_ID)
    p.add_argument('--public', action='store_true')
    p.add_argument('--require-assets', action='store_true')
    args = p.parse_args()
    identity(args.tag, args.commit, args.release_id)
    if args.command == 'checksums':
        checksums(args.directory, args.tag)
    elif args.command == 'verify':
        verify(args.directory, args.repo, args.commit, args.tag)
    else:
        verify_release_metadata(json.loads(Path(args.input).read_text()), args.public, args.require_assets,
                                args.tag, args.commit, args.release_id)
        print('Идентичность существующего release и состояние assets проверены.')


if __name__ == '__main__':
    main()
