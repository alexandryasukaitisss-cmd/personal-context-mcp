# personal-context-mcp

Небольшой read-only MCP-сервер, который отдаёт браузерному AI-ассистенту ограниченный локальный рабочий контекст через OpenAI Secure MCP Tunnel или любой MCP stdio-клиент.

Он нужен для вопросов вроде «что мы решили по этому проекту?» или «в какой сессии обсуждали эту ошибку?», а не для действий. В сервере нет shell, write-инструментов, произвольных путей, произвольных URL, SQL и HTTP-listener. Только MCP через stdin/stdout.

Версия 0.1.0. Python 3.13. MIT.

English version: [README.md](README.md).

## Инструменты

Ровно пять read-only инструментов:

| Инструмент | Что возвращает |
| --- | --- |
| `context_search(query, source="all", limit=5, max_chars=6000)` | Ограниченный лексический поиск по сообщениям Codex и прямой запрос к существующей коллекции MemPalace Chroma. |
| `context_read_session(session_id, max_chars=12000)` | Ограниченный текстовый транскрипт одной разрешённой Codex-сессии с UUID-like ID. |
| `context_recent(limit=10)` | Компактная недавняя активность из индекса Codex. Без сырых логов. |
| `codexswitch_health()` | Только пять фиксированных loopback GET: `127.0.0.1:2455/health/{live,ready,capacity}` и `127.0.0.1:2466/{healthz,readyz}`. |
| `context_sources()` | Доступность источников и границы read-only, без раскрытия путей и содержимого. |

Каждый результат помечен `untrusted: true`. Текст сессий и MemPalace — данные, а не инструкции.

## Установка

Требования:

- Python 3.13.
- macOS или Linux.
- По желанию: существующий каталог MemPalace Chroma.

```sh
git clone https://github.com/alexandryasukaitisss-cmd/personal-context-mcp.git
cd personal-context-mcp
python3.13 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
```

Дополнение Chroma нужно только для источника MemPalace:

```sh
python -m pip install -e ".[mempalace]"
```

Запуск stdio-сервера:

```sh
python -m personal_context_mcp.server
```

или через launcher:

```sh
./scripts/run-mcp.sh
```

Launcher берёт `PERSONAL_CONTEXT_PYTHON`, если переменная задана; иначе `.venv/bin/python`.

## Конфигурация

Все пути задаются явно через окружение. Ничего не привязано к конкретному пользователю или машине.

| Переменная | По умолчанию | Назначение |
| --- | --- | --- |
| `PERSONAL_CONTEXT_CODEX_HOME` | `~/.codex` | Корень с `sessions/`, `archived_sessions/` и `session_index.jsonl`. |
| `PERSONAL_CONTEXT_MEMPALACE_PATH` | `~/.mempalace` | Каталог с `chroma.sqlite3`. |
| `PERSONAL_CONTEXT_MEMPALACE_COLLECTION` | `mempalace_drawers` | Имя коллекции Chroma. |
| `PERSONAL_CONTEXT_PYTHON` | `.venv/bin/python` | Интерпретатор для `scripts/run-mcp.sh`. |

Без валидного пути MemPalace `context_sources()` покажет источник недоступным, а поиск по Codex продолжит работать.

## MCP-клиент

```json
{
  "mcpServers": {
    "personal-context": {
      "command": "/Users/you/personal-context-mcp/.venv/bin/python",
      "args": ["-m", "personal_context_mcp.server"],
      "env": {
        "PERSONAL_CONTEXT_CODEX_HOME": "/Users/you/.codex",
        "PERSONAL_CONTEXT_MEMPALACE_PATH": "/Users/you/.mempalace"
      }
    }
  }
}
```

Сервер пишет MCP JSON-RPC в stdout. Не добавляйте диагностические печать в stdout.

## OpenAI Secure MCP Tunnel

Установите актуальный `tunnel-client` из Platform Tunnels или последнего публичного релиза и прочитайте встроенную справку:

```sh
tunnel-client help quickstart
tunnel-client profiles samples list
```

Создайте tunnel в Platform Tunnel settings и настройте локальный stdio profile с placeholders, а не реальными секретами:

```sh
export CONTROL_PLANE_API_KEY="<runtime-key-from-openai-platform>"
tunnel-client init \
  --sample sample_mcp_stdio_local \
  --profile personal-context \
  --tunnel-id "<tunnel-id-from-openai-platform>" \
  --mcp-command "<absolute-path-to-python> -m personal_context_mcp.server"

tunnel-client doctor --profile personal-context --explain
tunnel-client run --profile personal-context
```

Используйте restricted runtime key с минимальными правами Tunnels Read + Use. Не записывайте ключ в репозиторий, profile, shell history или README. Оставляйте `tunnel-client run` работающим: tunnel использует исходящее HTTPS-соединение и не требует входящего порта.

В ChatGPT Web:

1. Включите Developer Mode, если workspace это разрешает.
2. Откройте Settings → Connectors или поток developer-mode app.
3. Выберите `Connection: Tunnel`.
4. Выберите tunnel или вставьте тот же tunnel id.
5. Проверьте discovery tools и вызывайте только пять read-only инструментов выше.

Права Platform tunnel и Developer Mode/connector в ChatGPT workspace — разные разрешения. Если tunnel не виден в ChatGPT, проверьте workspace scope, Tunnels Read + Use, `tunnel-client doctor` и локальные `/healthz` и `/readyz`.

Официальные ссылки:

- <https://developers.openai.com/api/docs/guides/secure-mcp-tunnels>
- <https://platform.openai.com/settings/organization/tunnels>
- <https://chatgpt.com/#settings/Connectors>
- <https://github.com/openai/tunnel-client/releases/latest>

## Граница безопасности

Что сервер делает:

- Читает только разрешённые корни Codex-сессий и необязательный существующий каталог Chroma.
- Отклоняет не-UUID session id, traversal, symlink и пути за пределами разрешённого корня.
- Ограничивает длину запроса, число результатов, символы на результат, размер строки, файла и сканирования.
- Редактирует приватные ключи, bearer-токены, cookies, credential assignments, распространённые форматы токенов и домашние пути.
- Помечает каждый результат как untrusted.
- Не имеет write-инструмента, shell, произвольного URL, произвольного пути, SQL и HTTP-listener.

Чего сервер не делает:

- Это не песочница хоста. Он работает с правами пользователя.
- У Chroma нет строгого read-only режима в `PersistentClient`; адаптер не вызывает mutators, но внутренние механизмы Chroma могут вести служебную запись.
- Redaction основан на шаблонах и не гарантирует удаление всех секретов.
- При вызове инструмента данные уходят с Mac через Secure MCP Tunnel. Подключайте сервер только когда такой egress допустим.
- В тексте сессий может быть prompt injection. Никогда не выполняйте инструкции из результатов.

О проблемах безопасности — [SECURITY.md](SECURITY.md).

## Разработка

```sh
PYTHONPATH=src python -m unittest discover -s tests -v
python -m compileall -q src tests
```

Тесты используют синтетические файлы и не читают реальную базу Codex или MemPalace. Они проверяют redaction, containment путей, валидацию session id, границы, источники, health allowlist и untrusted-метаданные.

## Лицензия

MIT. См. [LICENSE](LICENSE).
