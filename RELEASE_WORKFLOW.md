# Release Workflow

**Purpose**: Ensure every change—including emergency security fixes—reaches `master` only through the PR process.

---

## Standard Change Sequence

```
1. git checkout -b <type>/<description>     # branch off master
2. <make changes, commit locally>
3. git push origin <branch>                 # push feature branch
4. gh pr create --base master               # open PR
5. CI runs:  secret-scan → file-safety → code-security → dependency-audit
6. 2 approvals required (including CODEOWNERS where applicable)
7. All 4 status checks pass ✅
8. Merge via GitHub UI (squash or merge commit)
9. Delete feature branch
```

### Branch Naming

| Type | Pattern | Example |
|------|---------|---------|
| Feature | `feature/<name>` | `feature/new-badge-system` |
| Bug fix | `fix/<name>` | `fix/certificate-layout` |
| Security | `security/<name>` | `security/logging-redaction` |
| Docs | `docs/<name>` | `docs/governance-update` |
| Dependency | `deps/<name>` | `deps/bump-cryptography` |
| Hardening | `hardening/<name>` | `hardening/ci-scan-upgrade` |

---

## Emergency Security Fix Sequence

Even critical security fixes **MUST** go through a PR:

```
1. git checkout -b security/emergency-<cve-or-desc>
2. Apply minimal fix (smallest diff possible)
3. git push origin security/emergency-<desc>
4. gh pr create --base master --title "SEC-EMERGENCY: <desc>"
5. Tag @helpiran-security-team for expedited review
6. Approvers fast-track: 2 approvals within 1 hour target
7. CI checks MUST still pass (no bypass)
8. Merge immediately after approvals + checks
```

### What is NEVER Allowed

| Action | Allowed? | Why |
|--------|----------|-----|
| Direct push to `master` | ❌ **NEVER** | Branch protection prevents this |
| Disabling `enforce_admins` | ❌ **NEVER** | See Governance § Prohibited Actions |
| Bypassing CI checks | ❌ **NEVER** | Attackers exploit rushed merges |
| Force push to `master` | ❌ **NEVER** | Destroys audit trail |
| Merging with < 2 approvals | ❌ **NEVER** | No solo action allowed |

---

## If You Previously Bypassed Protection

If `enforce_admins` was temporarily disabled (as occurred during initial hardening):

1. **Document** what was pushed and why
2. **Verify** the commit contents are safe: `git log --oneline -5 && git diff HEAD~1`
3. **Re-enable** `enforce_admins` immediately:
   ```
   gh api -X POST repos/<owner>/<repo>/branches/master/protection/enforce_admins
   ```
4. **File an incident report** (see GOVERNANCE.md § Incident Reporting)
5. **Never repeat** — use the Emergency PR sequence above instead

---

## Verification Commands

Check branch protection is fully enforced:

```bash
gh api repos/<owner>/<repo>/branches/master/protection --jq '{
  approvals: .required_pull_request_reviews.required_approving_review_count,
  codeowners: .required_pull_request_reviews.require_code_owner_reviews,
  enforce_admins: .enforce_admins.enabled,
  checks: .required_status_checks.contexts,
  force_push: .allow_force_pushes.enabled,
  deletions: .allow_deletions.enabled
}'
```

Expected output:
```json
{
  "approvals": 2,
  "codeowners": true,
  "enforce_admins": true,
  "checks": ["secret-scan","file-safety","code-security","dependency-audit"],
  "force_push": false,
  "deletions": false
}
```

---

*Established: 2026-02-06. Any modification requires a governance-approved PR.*
