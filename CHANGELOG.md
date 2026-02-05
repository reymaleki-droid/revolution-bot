# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Security
- Added GitHub Actions security scanning workflow
- Added pre-commit hooks for secret detection
- Added Dependabot for automated dependency updates
- Created comprehensive THREAT_MODEL.md
- Enhanced CONTRIBUTING.md with security guardrails
- Added PR and issue templates with security checklists

## [1.1.0] - 2026-02-06

### Security
- **BREAKING**: Migrated from SQLite to PostgreSQL with zero-knowledge architecture
- Implemented HMAC-SHA256 user hashing (irreversible)
- Removed all PII storage (usernames, names, phone numbers)
- Added fail-closed configuration (missing secrets = exit)
- Added 30-day automatic data retention cleanup
- Moved insecure legacy code to `/legacy/` folder
- Created SECURITY.md with responsible disclosure process
- Added credential rotation documentation

### Added
- `secure_database_pg.py` - Zero-knowledge PostgreSQL database
- `verify_db.py` - Security verification script
- `smoke_test_db.py` - Runtime smoke tests
- Certificate generation system
- Physical rewards tracking
- Gamification with achievements and streaks

### Changed
- All database operations now use async/await
- User identifiers are hashed before storage
- Logs no longer contain user IDs
- Environment-only configuration (no hardcoded secrets)

### Removed
- Plaintext user ID storage
- Username and first_name storage
- File ID storage
- Message content storage

## [1.0.0] - 2026-01-27

### Added
- Initial release
- Email advocacy Mini App
- Conduit verification system
- Metadata stripping for videos/images
- Twitter campaign with spintax
- Gamification and leaderboard
- Full Persian UI

---

## Security Changelog Legend

- 🔴 **CRITICAL**: Immediate action required
- 🟠 **HIGH**: Address before next release
- 🟡 **MEDIUM**: Address in upcoming releases
- 🟢 **LOW**: Informational or minor impact

---

## Reporting Security Issues

See [SECURITY.md](SECURITY.md) for responsible disclosure process.

**DO NOT** open public issues for security vulnerabilities.
