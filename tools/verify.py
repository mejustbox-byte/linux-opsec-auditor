"""Nonempty test runner, source compilation, documentation links and secret-pattern checks.

This is a conservative repository guard, not a guarantee that no secret exists.
Never prints matched values. Only scans explicitly versioned project directories.
"""
import ast
import json
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from linux_opsec_auditor import __version__
from linux_opsec_auditor.schema import INPUT_SCHEMA


def checks():
    version = re.search(r'^version = "([^"]+)"$', (ROOT/'pyproject.toml').read_text(), re.MULTILINE).group(1)
    assert version == __version__, 'Несогласованная версия package'
    assert json.loads((ROOT/'schemas/input-v1.schema.json').read_text()) == INPUT_SCHEMA
    paths = [ROOT/'pyproject.toml', ROOT/'requirements-build.lock', ROOT/'LICENSE', ROOT/'MANIFEST.in']
    if (ROOT/'.gitignore').exists():
        paths.append(ROOT/'.gitignore')
    paths.extend(sorted(ROOT.glob('*.md')))
    for folder in ['src','tests','tools','docs','fixtures','schemas','.github']:
        paths.extend(p for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    # Split literals avoid the scanner matching its own pattern definitions.
    patterns = [re.compile('-----BEGIN ' + '(?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
                re.compile('gh' + '[pousr]_[A-Za-z0-9]{30,}'),
                re.compile('github_' + 'pat_[A-Za-z0-9_]{40,}'),
                re.compile('AK' + 'IA[A-Z0-9]{16}')]
    for path in paths:
        data=path.read_text(encoding='utf-8')
        assert not any(p.search(data) for p in patterns), f'Возможный секрет в {path.relative_to(ROOT)} (значение скрыто)'
        if path.suffix == '.py':
            compile(data,str(path),'exec')
            if 'src' in path.parts:
                tree=ast.parse(data)
                for node in ast.walk(tree):
                    if isinstance(node,(ast.Import,ast.ImportFrom)):
                        names=[n.name for n in node.names] if isinstance(node,ast.Import) else [node.module or '']
                        assert not any(n.split('.')[0] in {'subprocess','socket','requests','urllib','http'} for n in names), 'Команды/сеть запрещены в runtime'
        if path.suffix == '.md':
            assert re.search(r'[А-Яа-яЁё]',data), f'документ не содержит русского текста: {path.relative_to(ROOT)}'
            for link in re.findall(r'\[[^\]]+\]\(([^ )]+)\)',data):
                if '://' in link or link.startswith('#'):
                    continue
                assert (path.parent/link.split('#')[0]).exists(), f'Неверная внутренняя ссылка в {path.relative_to(ROOT)}'
    print(f'Проверки репозитория пройдены ({len(paths)} текстовых файлов); проверка паттернов не является исчерпывающим поиском секретов.',flush=True)


if __name__ == '__main__':
    checks()
    suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'))
    if suite.countTestCases() == 0:
        raise SystemExit('Тесты не найдены')
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)
