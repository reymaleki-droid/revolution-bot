## Description

<!-- Describe your changes in detail -->

## Type of Change

- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to change)
- [ ] Documentation update
- [ ] Security improvement

---

## Security Checklist

**⚠️ ALL ITEMS MUST BE CHECKED BEFORE MERGE ⚠️**

### Secrets & Credentials

- [ ] No API keys, tokens, or credentials in this PR
- [ ] No hardcoded passwords or secrets
- [ ] No `.env` files included
- [ ] No database connection strings
- [ ] No HASH_PEPPER or USER_HASH_SALT values

### Data Privacy

- [ ] No Telegram user IDs in code or comments
- [ ] No usernames or display names
- [ ] No personally identifiable information (PII)
- [ ] All user references use `_hash_user_id()` method
- [ ] Logging does not expose user identity

### Files

- [ ] No `.env` files (any variant)
- [ ] No `.db` or `.sqlite*` files
- [ ] No `.salt` files
- [ ] No certificate files with private keys
- [ ] No log files

### Code Quality

- [ ] Ran `pre-commit run --all-files` locally
- [ ] No security warnings from bandit
- [ ] All tests pass

---

## Testing

<!-- Describe how you tested your changes -->

- [ ] Unit tests added/updated
- [ ] Manual testing completed
- [ ] Tested with Railway environment

---

## Screenshots (if applicable)

<!-- Add screenshots for UI changes -->

---

## Additional Notes

<!-- Any additional information for reviewers -->
