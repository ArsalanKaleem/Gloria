# Security Checklist

This is the floor, not the ceiling. Production must exceed it.

## Authentication & authorization

- [x] API keys are stored as **bcrypt hashes**; only the prefix is queryable.
- [ ] Admin dashboard (once built) must be behind SSO or MFA.
- [ ] Role-based access controls (viewer / editor / auditor / super-admin).

## Transport & network

- [ ] HTTPS everywhere, HSTS enabled at the edge.
- [x] CORS allow-list is a comma-separated env var — set exact origins only.
- [ ] Firewall Postgres — only the backend container should reach 5432.

## Input handling

- [x] All request bodies validated by Pydantic; unknown fields rejected.
- [x] SQL access only through SQLAlchemy parametrised queries.
- [ ] Uploaded PDFs: check MIME + size cap, run a virus scan.

## LLM-specific risks

- [x] **Prompt injection.** System prompt explicitly forbids following
  instructions inside CONTEXT. Verify with an injection test set.
- [ ] **Document poisoning.** Only vetted admins upload. Consider an
  ingestion linter that flags unusual instruction-like content.
- [x] **Data exfiltration.** Model output does not include raw prompt
  fragments (nothing in the pipeline echoes the system prompt).

## Rate limiting & abuse

- [x] Per-IP rate limits via SlowAPI (`60/minute` default).
- [ ] Per-key daily quotas (`APIKey.daily_limit` column — enforce it).
- [ ] Alert when a single key issues 10× its daily average.

## Secrets, logs, privacy

- [ ] Secrets in a real secret manager (Vault / AWS SM / GCP SM). Not in Git.
- [ ] Logs redact PII, tokens, and API keys before writing.
- [ ] Chat log retention: ≤ 30 days by default; longer only with sign-off.
- [ ] Right-to-erasure endpoint that deletes user history and audits it.
