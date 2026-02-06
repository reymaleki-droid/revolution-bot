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

## Automated Emergency Merge (`scripts/emergency_merge.ps1`)

When the standard 2-approval workflow **cannot** be satisfied (e.g. single
maintainer, all reviewers unavailable during a security incident), use the
audited emergency merge script instead of ad-hoc API calls.

### Prerequisites — ALL must be true

| # | Condition | Verify |
|---|-----------|--------|
| 1 | The PR is **open** and all CI checks are **green** | Script validates automatically |
| 2 | The change is **security-critical** or blocks a production fix | Operator judgement |
| 3 | You have **admin** access to the repository | Required for API calls |
| 4 | No reviewer can provide approval within **1 hour** | Document in SEC-INCIDENT issue |

### Usage

```powershell
# Dry run — snapshots protection, validates PR, makes NO changes
.\scripts\emergency_merge.ps1 -PrNumber 15 -DryRun

# Live merge — lowers protection, merges, restores, writes audit log
.\scripts\emergency_merge.ps1 -PrNumber 15
```

### What the script does

| Phase | Action | Duration |
|-------|--------|----------|
| **1 — Snapshot** | Saves full branch protection JSON to `logs/protection-snapshot-*.json` and validates PR state + CI | Seconds |
| **2 — Lower** | Disables `enforce_admins`, sets approvals to 1 (keeps CODEOWNERS, keeps all status checks) | Seconds |
| **3 — Merge** | Squash-merges the PR and deletes the feature branch | Seconds |
| **4 — Restore** | Re-applies the **exact** original protection from the snapshot | Seconds |
| **5 — Audit** | Writes timestamped log to `logs/emergency-merge-audit-*.log` | Instant |

### After every use

1. **File a `SEC-INCIDENT` issue** (the script prints the exact command)
2. **Review the audit log** in `logs/` and attach it to the issue
3. **Verify protection** was restored: run the verification commands below

> ⚠️ **This script is a safety net, not a shortcut.** Every use is logged and
> must be justified. Abuse will result in repository access revocation per
> GOVERNANCE.md § Prohibited Actions.

---

## If You Previously Bypassed Protection (manually)

If `enforce_admins` was disabled via manual API calls (without the emergency
merge script):

1. **Document** what was pushed and why
2. **Verify** the commit contents are safe: `git log --oneline -5 && git diff HEAD~1`
3. **Re-enable** `enforce_admins` immediately:
   ```
   gh api -X POST repos/<owner>/<repo>/branches/master/protection/enforce_admins
   ```
4. **File an incident report** (see GOVERNANCE.md § Incident Reporting)
5. **Use `scripts/emergency_merge.ps1`** for any future emergency merges

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
