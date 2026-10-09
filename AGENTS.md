# Инструкции для следующих циклов

- Документация, release notes, пользовательские описания/help/schema и инструкции
  среды пишутся на русском. Код, команды, пути, JSON-ключи и ID не переводятся.
  Стандартный LICENSE MIT сохраняется; русский перевод — LICENSE.ru.md.
- Поддерживать полный индекс README и самостоятельные ARCHITECTURE, TECH-STACK,
  INSTALL, CONTRIBUTING, ROADMAP, SECURITY, CHANGELOG, THREAT-MODEL, CORE-CONTRACT,
  RUNBOOK, CLOUD-DEVELOPMENT, LOCAL-PC, VERIFICATION, RELEASE-CHECKLIST, RELEASE-NOTES.
  Сохранять docs/ и согласовывать смысл, ссылки и команды с реализацией.
- Использовать существующий изолированный checkout. Не создавать worktree без
  просьбы пользователя; сначала inspect status и сохранить чужие изменения.
- Read-only обязателен: никаких sudo, команд/сети в runtime, remediation, изменений
  хоста или автоматического production collect при старте. Новые collectors требуют
  ревью allowlist, схемы, OS/version scope и содержательных негативных тестов.
- Не печатать/сохранять credentials, реальные инвентари, raw infrastructure или private
  evidence в public git/logs/artifacts. Fixture — только synthetic. Pattern scan не
  доказывает абсолютного отсутствия секретов.
- Выполнять bash tools/setup_environment.sh и непустой набор tests. Проверять clean
  venv, frozen/hash install, source/wheel, runtime license inclusion и внутренние ссылки.
  TLS/checksum/assertions не отключать. Installer не должен зависеть от старого venv.
- Реально проверять head/CI/merge/tag/release ID/public state/assets/checksum/clean
  installation; не выдавать сохранённый draft или Git fallback за полный выпуск.
  Не передвигать старые tags; новая версия — новый tag из проверенного final main.
- Runtime source не аттестация. Не выдавать synthetic/containers/runner за live VM,
  kernel/LSM/systemd/restore evidence. В документах и release notes явно НЕ ВЫПОЛНЕНО
  для недоступных лабораторных gates и нового cloud snapshot restore.
- При разрешённом пользователем полном цикле продолжать до PR/CI/merge/assets без
  повторного запроса того же разрешения. Публикация использует штатный GITHUB_TOKEN
  с contents:write только в отдельном job. Не обходить auth и не создавать платные ресурсы.
- Обновлять русские install_script/start_skill среды, проверять их фактическое
  выполнение и сохранять draft. Сохранение не равно публикации snapshot/восстановлению.
