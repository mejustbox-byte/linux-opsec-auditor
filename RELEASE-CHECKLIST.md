# Контроль выпуска

0.1.0a1 сохранён, его tag не передвигается. Обновлённый prerelease: package 0.1.0a2,
tag v0.1.0-alpha.2 из финального main после отдельного русского PR/CI. Стабильный
release пока невозможен без реальных платформенных доказательств.

## До публикации

- README/pyproject/__version__/инструкции согласованы; документы на русском, ссылки
  существуют, команды соответствуют реализации. LICENSE сохраняет условия MIT.
- Непустые unit/integration и publication guards, новый venv, hash-locked install,
  wheel/sdist, isolated wheel smoke и reproducibility проходят. Lockfile не меняется.
- CI финального head прошёл Python 3.12/3.13; PR слит без обхода проверок.
- Финальный main SHA записан; новый tag указывает ровно на него. Старые tags не менять.
- Создать один draft prerelease с указанным tag/commit; получить его ID. При повторе
  использовать тот же ID, не дублировать release.
- Workflow запускается из main с явными tag/commit/ID. Build имеет read права,
  publish — ограниченное contents:write со штатным GITHUB_TOKEN, без новых secrets.

## Проверка assets и public состояния

1. Сборка именно проверенного commit; совпадение tag/HEAD и версии package.
2. Wheel/source содержат точные tagged files; нет extra modules/dependencies.
3. SHA256SUMS покрывает оба файла; в transfer нет недостающих outputs.
4. Проверить ID/tag/commit текущего release и живой remote tag. При обновлении assets
   release временно draft; только известные имена заменяются при повторе.
5. Скачать три native assets обратно, проверить metadata/state/size, SHA256 и source.
6. Только после этих проверок опубликовать тот же prerelease с русскими notes;
   снова проверить public state, assets и неизменность tag.
7. Независимо скачать публичные assets и установить wheel в новый venv вне checkout,
   выполнить version и свежую synthetic демонстрацию. Не заменять это Git fallback.

Публичный release без assets, один draft или отдельная artifact branch не завершают
выпуск. Ошибка оставляет проверяемый draft; не обходить аутентификацию/verification.
В финальном отчёте нужны PR/merge/CI/release/workflow ссылки и невыполненные VM-проверки.
Автоматизация — [docs/release-workflow](docs/release-workflow.md), запуск — [INSTALL](INSTALL.md).
