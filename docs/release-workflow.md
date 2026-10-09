# Проверенная публикация native assets

Cloud upload вернул 401; новые credentials и обход auth не применялись. Штатный
Actions GITHUB_TOKEN успешно завершил assets 0.1.0a1. Новый 0.1.0a2 публикуется тем
же ограниченным процессом, но из нового final main/tag; старый выпуск не перепаковывается.

Workflow manual-only из main. Входы: tag из разрешённых v0.1.0-alpha.1/2,
expected_commit — полный SHA, release_id — ID существующего draft/public release.
Package версии явно сопоставлены 0.1.0a1/a2. Неверный ввод отвергается до выполнения
product code; commit должен быть в истории проверенного dispatch main и совпасть с tag.
Workflow сам не создаёт release и никогда не создаёт/двигает/удаляет tag.

Build job contents:read: отдельный checkout reviewed automation и exact product,
hash-locked tools, непустые tests, build, installed-wheel smoke, reproducibility,
сравнение source/wheel/license с Git. Только три файла передаются SHA-pinned Actions.
Publish job contents:write: повторная проверка, живой tag, существующий ID/tag/commit,
перевод этого release в draft при upload, только известные имена при --clobber.

Затем все три native assets скачиваются обратно: uploaded state/size, SHA256,
содержимое Git, license bytes и MIT metadata проверяются. Только после успеха тот же
release становится публичным prerelease с русскими notes. Проверки после публикации
подтверждают public/assets/tag. Draft читается по числовому ID, не endpoint tag lookup.

```bash
gh workflow run release.yml --repo mejustbox-byte/linux-opsec-auditor --ref main \
  -f tag=v0.1.0-alpha.2 -f expected_commit=FULL_MAIN_SHA -f release_id=EXISTING_RELEASE_ID
gh run list --repo mejustbox-byte/linux-opsec-auditor --workflow release.yml
```

FULL_MAIN_SHA и EXISTING_RELEASE_ID — значения проверенного финального main и
единственного подготовленного release, не credentials. На повторе использовать тот
же ID. Не считать build-only success, пустой draft или Git fallback полным выпуском.
Ошибка оставляет draft для диагностики; tags не меняются. Платные ресурсы не создаются.

Независимая проверка после публикации:

```bash
opsec_release_dir=$(mktemp -d)
gh release download v0.1.0-alpha.2 --repo mejustbox-byte/linux-opsec-auditor \
  --dir "$opsec_release_dir" --pattern 'linux_opsec_auditor-0.1.0a2*' --pattern SHA256SUMS
python3 tools/release_artifacts.py verify --directory "$opsec_release_dir" --repo . \
  --tag v0.1.0-alpha.2 --commit FULL_MAIN_SHA
```

В shallow checkout сначала получить tag/commit. Wheel не имеет extra modules/runtime
dependencies; source содержит exact tagged files и допустимые generated metadata.
Нужно подтвердить LICENSE и LICENSE.ru.md в metadata/bytes. Реальные платформенные
gates остаются НЕ ВЫПОЛНЕНО — [лаборатория](laboratory.md), полный [checklist](../RELEASE-CHECKLIST.md).
