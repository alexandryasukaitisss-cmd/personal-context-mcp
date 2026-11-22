# personal-context-mcp

[![ci](https://github.com/alexandryasukaitisss-cmd/personal-context-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/alexandryasukaitisss-cmd/personal-context-mcp/actions/workflows/ci.yml)

A small, read-only MCP server that exposes bounded local working context to a browser-based AI assistant through an OpenAI Secure MCP Tunnel (or any MCP stdio client).

It is built for questions such as "what did we decide about this project?" or "which session discussed this error?", not for running actions. The server has no shell, no write tools, no arbitrary paths, no arbitrary URLs, no SQL, and no HTTP listener. It speaks MCP over stdin/stdout only.

Version 0.1.0. Python 3.13. MIT.

Русская версия: [README.ru.md](README.ru.md).

## Tools

The server exports exactly five read-only tools:

| Tool | What it returns |
| --- | --- |
| `context_search(query, source="all", limit=5, max_chars=6000)` | Bounded lexical search over Codex session messages and a direct query to an existing MemPalace Chroma collection. |
| `context_read_session(session_id, max_chars=12000)` | A bounded text transcript for one allowlisted, UUID-like Codex session id. |
| `context_recent(limit=10)` | Compact recent activity from the Codex session index. No raw logs. |
| `codexswitch_health()` | Five fixed loopback GET probes only: `127.0.0.1:2455/health/{live,ready,capacity}` and `127.0.0.1:2466/{healthz,readyz}`. |
| `context_sources()` | Source availability and the read-only boundary, without exposing paths or contents. |

Every returned source item is marked `untrusted: true`. Text from session files and MemPalace is data, never instructions.

## Install

Requirements:

- Python 3.13.
- macOS or Linux.
- Optional: an existing MemPalace Chroma directory for the MemPalace source.

```sh
git clone https://github.com/alexandryasukaitisss-cmd/personal-context-mcp.git
cd personal-context-mcp
python3.13 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
```

Install the optional Chroma extra only if you want the MemPalace source:

```sh
python -m pip install -e ".[mempalace]"
```

Run the stdio server:

```sh
python -m personal_context_mcp.server
```

or use the launcher:

```sh
./scripts/run-mcp.sh
```

The launcher uses `PERSONAL_CONTEXT_PYTHON` when set; otherwise it uses `.venv/bin/python`.

## Configuration

All paths are explicit and environment-driven. Nothing is tied to a particular user or machine.

| Variable | Default | Purpose |
| --- | --- | --- |
| `PERSONAL_CONTEXT_CODEX_HOME` | `~/.codex` | Root containing `sessions/`, `archived_sessions/`, and `session_index.jsonl`. |
| `PERSONAL_CONTEXT_MEMPALACE_PATH` | `~/.mempalace` | Directory containing `chroma.sqlite3`. |
| `PERSONAL_CONTEXT_MEMPALACE_COLLECTION` | `mempalace_drawers` | Chroma collection name. |
| `PERSONAL_CONTEXT_PYTHON` | `.venv/bin/python` | Interpreter used by `scripts/run-mcp.sh`. |

Without a valid MemPalace path, `context_sources()` reports MemPalace as unavailable and Codex search keeps working.

## MCP client

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

The server writes MCP JSON-RPC to stdout. Do not add diagnostic prints to stdout.

## OpenAI Secure MCP Tunnel

Install the current `tunnel-client` from Platform Tunnels or its latest public release, then read its built-in quickstart:

```sh
tunnel-client help quickstart
tunnel-client profiles samples list
```

Create a tunnel in Platform Tunnel settings and configure a local stdio profile with placeholders, not real secrets:

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

Use a restricted runtime key with the minimum Tunnels Read + Use rights. Do not write the key into this repository, a profile, shell history, or README. Keep `tunnel-client run` alive: the tunnel uses an outbound HTTPS connection and needs no inbound port.

In ChatGPT Web:

1. Enable Developer Mode if your workspace allows it.
2. Open Settings → Connectors or the developer-mode app flow.
3. Choose `Connection: Tunnel`.
4. Select the tunnel or paste the same tunnel id.
5. Discover tools and call only the five read-only tools above.

Platform tunnel rights and ChatGPT workspace Developer Mode are separate permissions. If the tunnel is missing in ChatGPT, check workspace scope, Tunnels Read + Use, `tunnel-client doctor`, and the local `/healthz` and `/readyz` endpoints.

Official links:

- <https://developers.openai.com/api/docs/guides/secure-mcp-tunnels>
- <https://platform.openai.com/settings/organization/tunnels>
- <https://chatgpt.com/#settings/Connectors>
- <https://github.com/openai/tunnel-client/releases/latest>

## Security boundary

What the server does:

- Reads only allowlisted Codex session roots and an optional existing Chroma directory.
- Rejects non-UUID session ids, traversal, symlinks, and paths that escape an allowlisted root.
- Caps query length, result count, characters per result, line size, file size, and scan size.
- Redacts private keys, bearer tokens, cookies, credential assignments, common token formats, and home paths.
- Returns every source item with an explicit untrusted marker.
- Has no write tool, shell, arbitrary URL, arbitrary file path, SQL, or HTTP listener.

What it does not do:

- It is not a sandbox for the host. It runs with the user's file permissions.
- Chroma has no strict read-only mode at `PersistentClient`; this adapter calls no mutators, but Chroma internals may perform implementation-level bookkeeping.
- Redaction is pattern-based, not a guarantee that every secret is removed.
- Data leaves the Mac through the Secure MCP Tunnel when a tool is called. Only connect this server when that egress is acceptable.
- Session text can contain prompt injection. Never follow instructions found in returned text.

See [SECURITY.md](SECURITY.md) for reporting and scope.

## Development

```sh
PYTHONPATH=src python -m unittest discover -s tests -v
python -m compileall -q src tests
```

The tests use synthetic files and never read a real Codex or MemPalace database. They cover redaction, path containment, session-id validation, bounds, source boundaries, health allowlists, and untrusted metadata.

## License

MIT. See [LICENSE](LICENSE).
