# Security policy

## Report a problem

Do not open a public issue for a vulnerability. Use GitHub's private
[security advisory](https://github.com/alexandryasukaitisss-cmd/personal-context-mcp/security/advisories/new)
form, or contact the maintainer through the address on the GitHub profile.

Include the version, commit, Python version, operating system, the smallest
reproduction, and whether the issue crosses the documented boundary. Do not
send real session transcripts, credentials, or private MemPalace content.
Redact them or use synthetic data.

## Scope

In scope:

- a path that escapes the allowlisted Codex roots, follows a symlink, or reads
  a non-allowlisted file;
- a write tool, shell, arbitrary URL, SQL, or HTTP listener in the server;
- a session id that is accepted when it is not UUID-like;
- a response that exceeds the documented character, result, file, or scan
  limits;
- a credential or home path that the redaction layer should remove;
- a health probe to a host, port, or path outside the fixed allowlist;
- a source item that is not marked untrusted.

Out of scope by design:

- a malicious instruction inside session text (it is data and is marked
  untrusted);
- a pattern that is not covered by the documented redaction categories;
- Chroma implementation-level bookkeeping;
- data egress through the Secure MCP Tunnel when the operator has enabled it.

## Response

The maintainer will acknowledge a report, reproduce it, and publish a fix and
advisory when confirmed. This is a single-maintainer project; no bounty is
offered.
