# Public-data and privacy notes

## What belongs in this repository

This public portfolio is assembled from an allowlist of source code, dependency files, tests, documentation, and demonstration scripts. It begins with a fresh Git history. Runtime artifacts and private materials are excluded from the public set.

The demonstration brand **Northstar**, its `northstar.example` URLs, sample records, and simulated AI responses are fictional. They are examples of data shape and application behavior, not factual brand research or evidence of a customer relationship.

## Excluded materials

- API credentials, tokens, real environment files, and private configuration.
- Databases, database exports, backups, logs, and application state.
- Uploaded assets, customer documents, correspondence, and internal working materials.
- Local virtual environments, caches, machine-specific paths, and previous Git history.

The checked-in `.env.example` contains configuration placeholders. `.env`, `portfolio_demo.db`, and `uploads/` are local runtime material and must stay outside the public commit set. Ignore rules help avoid accidental additions; they do not remove a file that has already been tracked.

## Runtime data flow

| Operation | Data used | Destination |
| --- | --- | --- |
| Offline demonstration | Synthetic records and simulated AI output | Isolated in-memory SQLite and terminal output |
| Local record and evidence routes | Records entered by the local user | Local `portfolio_demo.db` and API responses |
| File upload routes | Files intentionally uploaded by the local user | Local `uploads/` directory |
| Optional live brand research | Requested brand name and research instructions | OpenAI API; returned preview is temporarily cached in process memory |
| Optional live product analysis | Product name/type and optional image URL or image content | OpenAI API; mapped analysis is saved locally |

An image stored on disk can be encoded and sent as image content during live product analysis. A local file path does not mean that its content stays local once that feature is invoked. Use only material you are authorized to submit. This project does not promise a provider-side retention policy or implement a complete deletion and retention system.

The offline demonstration does not use live credentials or contact the AI provider. Local CRUD and evidence retrieval do not require an API key. Installing dependencies is a separate network operation.

## Before a public release

Run from the repository root:

```bash
python scripts/check_public_release.py
```

Also review the exact files and changes intended for the commit. The checker uses filename rules and text patterns to detect common accidental disclosures. It can miss unfamiliar identifiers, secrets with unexpected formats, content outside its scan scope, or sensitive meaning that requires human context. A successful scan is a useful check, not a confidentiality guarantee.

Review new examples for identifying names, domains, contact details, account references, file metadata, and copied text. Keep replacement examples fully synthetic rather than partially masking real records. Fresh history prevents old commits from being included in this initial release, but later commits need the same care.

## If sensitive information is published

Revoke exposed credentials first. Remove the affected content and assess repository history, downloadable artifacts, and any copies that may already exist. Deleting a file from the latest commit does not remove older public copies. Do not paste sensitive material into a public issue while reporting the problem.
