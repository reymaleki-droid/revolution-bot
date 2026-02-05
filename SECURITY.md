# Security Policy

> **This project is designed to fail safely.**

---

## 🔒 Trust Signals

| Signal | Status | Verification |
|--------|--------|--------------|
| Open Source | ✅ | Full code visible |
| Zero-Knowledge DB | ✅ | Inspect `secure_database_pg.py` |
| Signed Commits | ✅ | GPG-verified authors |
| Branch Protection | ✅ | 2 approvals required |
| No Secrets in Repo | ✅ | Automated CI scanning |
| Threat Model | ✅ | See [THREAT_MODEL.md](THREAT_MODEL.md) |
| Kill Switch | ✅ | See [KILL_SWITCH.md](KILL_SWITCH.md) |
| Governance | ✅ | See [GOVERNANCE.md](GOVERNANCE.md) |

---

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it responsibly:

1. **DO NOT** open a public GitHub issue
2. Email: [Create a private security advisory on GitHub]
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

We will respond within 48 hours and work with you to understand and address the issue.

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |

## Security Model

This bot implements a **zero-knowledge architecture**:

### What We DO Store
- HMAC-SHA256 hashed user identifiers (irreversible)
- Points, ranks, and action timestamps
- Aggregate statistics (no individual attribution)

### What We NEVER Store
- Telegram user IDs (plaintext)
- Usernames or display names
- Phone numbers or email addresses
- Message content or media files
- File IDs or Telegram-internal identifiers
- IP addresses or location data
- OCR text from verification screenshots

### Security Measures
- All user identifiers are hashed with HMAC-SHA256 + pepper + salt
- Secrets loaded exclusively from environment variables
- Parameterized SQL queries (no injection risk)
- Fail-closed design (missing secrets = exit)
- 30-day automatic data retention cleanup
- No logging of PII

## Threat Model

### Protected Against
- Database breach → only hashed IDs, no PII recovery possible
- Log analysis → no user identifiers logged
- Memory dump → secrets in env vars, not code
- Rainbow tables → unique salt + pepper per deployment

### Out of Scope
- Telegram API security (Telegram's responsibility)
- Server/hosting infrastructure security
- Denial of service attacks
- Social engineering against admins

## Credential Rotation Policy

### DATABASE_URL

The `DATABASE_URL` contains embedded PostgreSQL credentials. If compromised:

1. **Railway does NOT support in-place credential rotation**
2. Required remediation:
   ```
   a) Create a NEW PostgreSQL service in Railway
   b) Migrate data using pg_dump/pg_restore
   c) Update DATABASE_URL in bot service
   d) Redeploy application
   e) Delete old PostgreSQL service
   ```
3. This causes downtime and carries migration risk
4. **Prevention is key** - never log or expose DATABASE_URL

### BOT_TOKEN

If the Telegram bot token is compromised:

1. Go to @BotFather on Telegram
2. Use `/revoke` to revoke the old token
3. Use `/token` to generate a new token
4. Update `BOT_TOKEN` in Railway environment
5. Redeploy the application

### HASH_PEPPER and USER_HASH_SALT

**These MUST NEVER be rotated** after production deployment:
- Changing them invalidates ALL existing user hashes
- Users would lose their points, ranks, and history
- Store backups securely but never commit to code

## Verification

You can independently verify the security model by:

1. Inspecting `secure_database_pg.py` - all `_hash_user_id()` calls
2. Checking database schema - no PII columns exist
3. Running `verify_db.py` - automated security checks
4. Reviewing logs - no user identifiers present

---

## ⚠️ Failure Scenarios & User Safety

### What happens if GitHub is compromised?

| Impact | User Safety |
|--------|-------------|
| Attacker could inject code | Requires 2 approvals (delayed) |
| Attacker could access repo settings | No production secrets in GitHub |
| Attacker could modify workflows | CI has no production access |

**User data safety**: ✅ PRESERVED - No user data in repository

**Mitigation**: Fork to trusted location, rotate all secrets

### What happens if ALL maintainers are compromised?

| Impact | User Safety |
|--------|-------------|
| Could merge malicious code | Public audit trail exists |
| Could access Railway secrets | User hashes still protected |
| Could impersonate bot | Revoke via @BotFather |

**User data safety**: ✅ PRESERVED - Database has only hashed IDs

**Mitigation**: 
1. Community forks repository
2. New trusted maintainers established
3. Users switch to new bot
4. No historical data is lost (none exists)

### What happens if CI is malicious?

| Impact | User Safety |
|--------|-------------|
| Could inject build artifacts | Requires PR approval first |
| Could exfiltrate repo secrets | No production secrets in CI |
| Could fail silently | Manual verification possible |

**User data safety**: ✅ PRESERVED - CI has zero production access

**Mitigation**: Disable Actions, review workflows, restore from known-good

---

## What Users LOSE in Worst Case

| Scenario | User Loses |
|----------|------------|
| Database breach | Points/ranks (non-sensitive) |
| Bot compromise | Trust in bot (until replaced) |
| Full infrastructure failure | Service availability |

## What Users NEVER Lose

| Protected | Why |
|-----------|-----|
| Identity | Never stored |
| Messages | Never stored |
| Location | Never collected |
| Contacts | Never accessed |
| Files | Never persisted |

---

## Why Trust Still Holds

Even in a catastrophic failure:

1. **Mathematically irreversible hashing** - User IDs cannot be recovered from hashes without the pepper AND salt AND brute-forcing billions of possibilities

2. **No PII by design** - The database schema physically cannot store usernames, names, or contact info

3. **Defense in depth** - Multiple independent layers must ALL fail for user safety to be compromised

4. **Fork rights** - Anyone can fork and audit; trust is distributed, not centralized

5. **Transparency** - All code, all changes, all decisions are public

---

## Liability Limitations

This security policy is provided for transparency, not as a warranty.

| Provided | Not Provided |
|----------|--------------|
| Best-effort security | Guarantees against all attacks |
| Transparent disclosure | Legal protection for users |
| Documented threat model | Insurance or indemnification |
| Rapid response process | SLA or uptime guarantees |

**By using this software, you accept that:**
- No system is perfectly secure
- You are responsible for your deployment
- Contributors are not liable for damages
- This is provided "AS IS" under MIT License

---

*Security is a process, not a destination. We commit to transparency, rapid response, and continuous improvement.*
