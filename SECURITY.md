# Security boundaries

## Supported use

This repository is an engineering portfolio prototype for local inspection with synthetic data. No version is presented as production-hardened or approved for public deployment.

Start the example server on the loopback interface:

```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

## Known limitations

- The API has no authentication, authorization, or rate limiting. A caller who can reach it can invoke its available read and write operations.
- File uploads, external URLs, and AI output require further validation before processing untrusted material. Do not treat model instructions or citation links as a security boundary.
- Live AI routes can send submitted information to an external provider and incur charges. The research cache is not a spending limit.
- SQLite persistence and startup table creation do not supply schema migrations, audit history, backups, or a recovery procedure.
- Tests exercise selected behaviors. They do not constitute a penetration test, dependency audit, or complete validation of database integrity and concurrency.
- Generated analyses are not reviewed automatically. Their confidence values and factual claims have not been independently calibrated or evaluated.

Keep credentials in the local environment or ignored `.env` file. Keep databases and uploads out of commits. See [public-data and privacy notes](docs/privacy.md) for release boundaries and external data flows.

## Reporting a problem

For a non-sensitive defect, open an issue with a minimal synthetic reproduction, expected behavior, and the affected code location. Do not include tokens, real records, private files, or exploitable deployment details in a public issue.

If the repository offers a private vulnerability-reporting channel, use it for sensitive findings. If no private channel is available, request a private contact method without posting the sensitive details. This document does not imply a response-time guarantee or an established security response team.
