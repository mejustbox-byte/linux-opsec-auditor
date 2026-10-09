# Модель угроз продукта

Цель: не повредить хост, не раскрыть инфраструктуру и не создать ложную уверенность.
Границы доверия: оператор/снимок и файлы → schema → evaluator → report → публичный git.
Runtime на скомпрометированном хосте не доказывает собственную честность. source —
утверждение поставщика, не подпись; даже свежий runtime source не аттестация.

Основные контроли: закрытые поля/типы, лимит 1 MiB, duplicate/date/range validation,
фиксированные read sources, O_PATH/nofollow/fd, отсутствие sudo/команд/сети,
отдельные unknown/not_run, красная граница static/runtime и приватная O_EXCL 0600 запись.
Отчёт содержит лишь разрешённые факты; baseline digest заменён equality. Ошибки не
выводят payload/пути ОС. Примеры исключительно synthetic; raw reports в public git запрещены.

Остаточные риски: kernel/mount может подделывать чтения; ФС может зависнуть без жёсткого
deadline; mode bits не отражают ACL/parents; Include/Match не разрешены; backup restore
и delivery доверены внешнему evidence. atime/audit эффекты чтения возможны. Оператор
может сам утечь через stdout; даже boolean posture чувствителен.

CI tests имеют contents:read. Публикация из main использует отдельный job contents:write
и штатный GITHUB_TOKEN; tag/commit/ID/скачанные assets проверяются до public состояния.
Нет pull_request_target с недоверенным кодом или новых credentials. Python/runner,
подписанный ли vendor feed и approved ли baseline — отдельные корни доверия.

Полная таблица угроз/контролей/проверок — [подробная модель](docs/threat-model.md).
Приватное сообщение об уязвимости — [SECURITY](SECURITY.md); remediation не реализуется.
