# Contributing to National Revolution 1404 Bot

Thank you for your interest in contributing! This project serves **high-risk users** (activists, journalists, human rights defenders). Security is not optional—it's the core mission.

> ⚠️ **Before contributing, read [THREAT_MODEL.md](THREAT_MODEL.md) to understand what we're protecting against.**

---

## 🚫 FORBIDDEN ACTIONS

These actions are **strictly prohibited** and will result in immediate PR rejection:

### NEVER commit:

| Forbidden | Example | Why |
|-----------|---------|-----|
| Environment files | `.env`, `.env.local`, `.env.prod` | Contains secrets |
| API tokens | `BOT_TOKEN=8537...` | Bot compromise |
| Database credentials | `DATABASE_URL=postgres://...` | Data exposure |
| Salt/pepper values | `HASH_PEPPER=abc123...` | Breaks anonymity |
| Database files | `*.db`, `*.sqlite`, `*.sqlite3` | Contains user data |
| Salt files | `*.salt`, `user_hash.salt` | Cryptographic material |
| Log files | `*.log`, `bot.log` | May contain PII |
| User IDs | `user_id = 123456789` | Identifies real users |
| Usernames | `username = "activist_user"` | PII exposure |
| Certificate keys | `*.pem`, `*.key` (private) | Cryptographic material |

### NEVER in code:

```python
# ❌ FORBIDDEN - Hardcoded user ID
ADMIN_ID = 123456789

# ❌ FORBIDDEN - Logging user identity  
logger.info(f"User {user_id} submitted content")

# ❌ FORBIDDEN - Storing plaintext
await conn.execute("INSERT INTO users (user_id) VALUES ($1)", user_id)

# ❌ FORBIDDEN - Including secrets
BOT_TOKEN = "1234567890:XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
```

---

## 🔒 Security Requirements

### Pre-Commit Checklist

**Run before EVERY commit:**

```bash
# Install pre-commit hooks (first time only)
pip install pre-commit
pre-commit install

# Run all checks manually
pre-commit run --all-files
```

### Before You Commit

**NEVER commit:**
- `.env` files (any environment files with real values)
- Bot tokens, API keys, or passwords
- Database credentials or connection strings
- User data, logs, or database files
- Salt files (`*.salt`, `user_hash.salt`)

**ALWAYS verify:**
```bash
# Check what you're about to commit
git status
git diff --cached

# Verify no secrets in staged files
git diff --cached | grep -iE "(token|password|secret|api_key|database_url)"
```

### Code Review Checklist

Before submitting a PR, ensure:

- [ ] No hardcoded secrets or credentials
- [ ] No logging of user IDs, usernames, or PII
- [ ] No storage of plaintext identifiers
- [ ] All user identifiers use `_hash_user_id()`
- [ ] Error messages don't leak internal details
- [ ] New features follow zero-knowledge principles

## 🏗️ Architecture Rules

### Zero-Knowledge Database

All database operations MUST:
1. Hash user IDs with `_hash_user_id()` before storage
2. Never store usernames, first names, or phone numbers
3. Never store file_ids or message content
4. Use parameterized queries only

```python
# ✅ CORRECT
user_hash = self._hash_user_id(user_id)
await conn.execute("INSERT INTO users (user_hash, points) VALUES ($1, $2)", user_hash, 100)

# ❌ WRONG - Never do this
await conn.execute("INSERT INTO users (user_id, username) VALUES ($1, $2)", user_id, username)
```

### Logging

Logs MUST NOT contain:
- User IDs (use "identity protected" placeholder)
- Usernames or display names
- Message content
- Token or credential values
- Database query parameters with user data

```python
# ✅ CORRECT
logger.info("User action completed (identity protected)")

# ❌ WRONG
logger.info(f"User {user_id} performed action")
```

## 🧪 Testing

### Local Development

1. Copy `.env.example` to `.env`
2. Fill in your test values (local only)
3. Use `docker-compose up` for local PostgreSQL
4. Run tests: `python -m pytest`

### Security Testing

Before any PR:
```bash
# Run security verification
python verify_db.py

# Run smoke tests
python smoke_test_db.py

# Check for secrets
grep -rn "BOT_TOKEN\|password\|secret" --include="*.py" | grep -v "os.getenv\|\.example"
```

## 📝 Pull Request Process

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make changes following security guidelines
4. Test thoroughly
5. Commit with clear messages
6. Push and create PR

### PR Requirements

**Every PR must pass this checklist (enforced by template):**

#### Secrets & Credentials
- [ ] No API keys, tokens, or credentials in this PR
- [ ] No hardcoded passwords or secrets
- [ ] No `.env` files included
- [ ] No database connection strings
- [ ] No HASH_PEPPER or USER_HASH_SALT values

#### Data Privacy
- [ ] No Telegram user IDs in code or comments
- [ ] No usernames or display names
- [ ] No personally identifiable information (PII)
- [ ] All user references use `_hash_user_id()` method
- [ ] Logging does not expose user identity

#### Files
- [ ] No `.env` files (any variant)
- [ ] No `.db` or `.sqlite*` files  
- [ ] No `.salt` files
- [ ] No certificate files with private keys
- [ ] No log files

#### Code Quality
- [ ] Ran `pre-commit run --all-files` locally
- [ ] No security warnings from bandit
- [ ] All tests pass

---

## 🛡️ CI/CD Security

All PRs are automatically scanned for:

| Check | Tool | Blocks PR |
|-------|------|-----------|
| Secrets in code | Gitleaks | ✅ Yes |
| Telegram tokens | Custom regex | ✅ Yes |
| Database credentials | Custom regex | ✅ Yes |
| Forbidden files | File check | ✅ Yes |
| Python vulnerabilities | Bandit | ✅ Yes |
| Dependency CVEs | Safety | ⚠️ Warning |

**PRs that fail security checks cannot be merged.**

---

## 🚨 Reporting Security Issues

**DO NOT** open public issues for security vulnerabilities.

See [SECURITY.md](SECURITY.md) for responsible disclosure process.

---

## ⚖️ Contributor Liability & Agreement

By contributing to this project, you acknowledge and agree:

### You Grant

- **MIT License** to all your contributions
- Permission for others to use, modify, and distribute your code
- Right for maintainers to modify or reject your contributions

### You Accept

- **No liability** for how your code is used after merge
- **No liability** for other contributors' code
- **No liability** for deployment decisions by users
- **No warranty** is provided by you or expected from you

### You Understand

- This project serves **high-risk users** in potentially hostile environments
- Security mistakes can have real-world consequences
- Your contributions will be publicly visible forever
- You may be identified as a contributor (via git history)

### You Commit To

- Following the security guidelines in this document
- Not intentionally introducing vulnerabilities
- Disclosing any conflicts of interest
- Reporting security issues responsibly

---

## 📜 License

All contributions are licensed under the **MIT License**.

See [LICENSE](LICENSE) for full terms.
