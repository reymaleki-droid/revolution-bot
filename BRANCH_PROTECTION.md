# Branch Protection Rules — Required Configuration

**Repository**: National Revolution 1404 Bot  
**Branch**: `main` (production)  
**Last Updated**: February 2026  

---

## ⚠️ MANDATORY SETTINGS

These settings MUST be enabled before the repository goes public.  
Failure to enable these creates single-point-of-failure risks.

---

## GitHub Settings Path

`Settings → Branches → Add branch protection rule`

**Branch name pattern**: `main`

---

## Required Toggles

### Pull Request Requirements

| Setting | Value | Rationale |
|---------|-------|-----------|
| **Require a pull request before merging** | ✅ ON | Prevents direct pushes to main; forces review |
| **Require approvals** | ✅ ON | No solo merges |
| **Required number of approvals** | `2` | Prevents single-maintainer abuse |
| **Dismiss stale pull request approvals when new commits are pushed** | ✅ ON | Prevents bait-and-switch attacks |
| **Require review from Code Owners** | ✅ ON | Ensures designated reviewers see changes |
| **Require approval of the most recent reviewable push** | ✅ ON | Prevents last-minute unreviewed changes |

### Status Checks

| Setting | Value | Rationale |
|---------|-------|-----------|
| **Require status checks to pass before merging** | ✅ ON | CI must pass |
| **Require branches to be up to date before merging** | ✅ ON | Prevents merge of stale branches |
| **Status checks that are required** | `secret-scan`, `file-safety`, `code-security` | All security checks must pass |

### Commit Requirements

| Setting | Value | Rationale |
|---------|-------|-----------|
| **Require signed commits** | ✅ ON | Cryptographic proof of author identity |
| **Require linear history** | ✅ ON | Clean audit trail, no merge commits hiding changes |

### Administrator Enforcement

| Setting | Value | Rationale |
|---------|-------|-----------|
| **Do not allow bypassing the above settings** | ✅ ON | Even admins cannot bypass |
| **Include administrators** | ✅ ON | No special privileges |

### Push/Delete Restrictions

| Setting | Value | Rationale |
|---------|-------|-----------|
| **Restrict who can push to matching branches** | ✅ ON | Only merge via PR |
| **Allow force pushes** | ❌ OFF | Prevents history rewriting |
| **Allow deletions** | ❌ OFF | Prevents branch destruction |

---

## CODEOWNERS File

Create `.github/CODEOWNERS`:

```
# All changes require review from security team
* @security-team

# Critical files require additional review
bot.py @security-team @core-maintainers
secure_database_pg.py @security-team @core-maintainers
config.py @security-team @core-maintainers
```

---

## Ruleset Alternative (GitHub Rulesets)

For enhanced control, use Repository Rulesets:

`Settings → Rules → Rulesets → New ruleset`

### Ruleset: `production-protection`

| Rule | Configuration |
|------|---------------|
| Target | `main` branch |
| Enforcement | Active |
| Bypass list | EMPTY (no bypasses) |
| Restrict deletions | ✅ |
| Require linear history | ✅ |
| Require signed commits | ✅ |
| Require pull request | 2 approvals, dismiss stale, require last push approval |
| Require status checks | All security checks |
| Block force pushes | ✅ |

---

## Verification Checklist

After enabling, verify:

- [ ] Direct push to `main` fails
- [ ] PR without approval cannot merge
- [ ] PR with failing CI cannot merge
- [ ] Force push is rejected
- [ ] Branch delete is rejected
- [ ] Admin bypass is blocked
- [ ] Unsigned commits are rejected

---

## Emergency Override

**There is no emergency override.**

If a critical fix is needed:
1. Create PR normally
2. Get 2 approvals
3. Wait for CI
4. Merge

If maintainers are unavailable:
1. Fork repository
2. Apply fix in fork
3. Users switch to fork temporarily
4. Coordinate proper merge when available

**The inconvenience is the security.**

---

## Audit Log

All branch protection changes are logged in:
`Settings → Security → Audit log`

Review monthly for unauthorized changes.
