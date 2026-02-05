# Governance Model

**Purpose**: Eliminate single-point-of-failure in project control  
**Principle**: No individual can compromise user safety alone  

---

## Roles and Permissions

### Role Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│                        COMMUNITY                            │
│  (Public oversight, issue reporting, fork rights)           │
├─────────────────────────────────────────────────────────────┤
│                       CONTRIBUTORS                          │
│  (Submit PRs, participate in discussions)                   │
├─────────────────────────────────────────────────────────────┤
│                        REVIEWERS                            │
│  (Approve/request changes on PRs, no merge rights)          │
├─────────────────────────────────────────────────────────────┤
│                       MAINTAINERS                           │
│  (Merge approved PRs, manage issues, no solo action)        │
├─────────────────────────────────────────────────────────────┤
│                     SECURITY TEAM                           │
│  (Required reviewer for security-sensitive files)           │
├─────────────────────────────────────────────────────────────┤
│                         OWNERS                              │
│  (Repository settings, member management)                   │
└─────────────────────────────────────────────────────────────┘
```

---

## Permission Matrix

| Action | Contributor | Reviewer | Maintainer | Security | Owner |
|--------|-------------|----------|------------|----------|-------|
| Submit PR | ✅ | ✅ | ✅ | ✅ | ✅ |
| Comment on PR | ✅ | ✅ | ✅ | ✅ | ✅ |
| Approve PR | ❌ | ✅ | ✅ | ✅ | ✅ |
| Merge PR | ❌ | ❌ | ✅* | ✅* | ✅* |
| Push to main | ❌ | ❌ | ❌ | ❌ | ❌ |
| Force push | ❌ | ❌ | ❌ | ❌ | ❌ |
| Delete branch | ❌ | ❌ | ❌ | ❌ | ❌ |
| Change settings | ❌ | ❌ | ❌ | ❌ | ✅** |
| Add members | ❌ | ❌ | ❌ | ❌ | ✅** |
| Access secrets | ❌ | ❌ | ❌ | ❌ | ❌*** |

`*` Requires 2 approvals + CI pass  
`**` Logged in audit trail, requires justification  
`***` Production secrets are in Railway only, not GitHub  

---

## What Each Role CANNOT Do

### Owner CANNOT:
- Merge without 2 approvals
- Push directly to main
- Force push or rewrite history
- Access production secrets (not in GitHub)
- Delete the main branch
- Bypass CI checks
- Act without audit trail

### Maintainer CANNOT:
- Merge their own PR without 2 other approvals
- Change repository settings
- Add/remove team members
- Bypass branch protection
- Access production environment

### Security Team CANNOT:
- Merge without another approval
- Change repository settings
- Access production secrets

### Reviewer CANNOT:
- Merge any PR
- Approve their own PR
- Access any administrative functions

---

## Minimum Viable Governance

| Requirement | Minimum |
|-------------|---------|
| Active Owners | 2 (neither can act alone) |
| Active Maintainers | 2 (for review requirement) |
| Security Team Members | 2 (for sensitive files) |
| PR Approvals Required | 2 |
| CI Checks Required | All |

---

## Transparency Requirements

### Public Visibility

| Item | Visibility |
|------|------------|
| All code | Public |
| All PRs | Public |
| All issues | Public |
| All discussions | Public |
| Audit log (settings changes) | Owners only (summarize monthly) |
| Production secrets | Not in repository |
| User data | Not in repository |

### Monthly Transparency Report

Owners SHOULD publish monthly:
- Number of PRs merged
- Number of security issues addressed
- Any settings changes made
- Any member role changes
- Any incidents

---

## Emergency Revocation Model

### If a maintainer is compromised:

1. **Any Owner** can remove the compromised maintainer
2. **Audit** all recent merges by that maintainer
3. **Rotate** any secrets they may have accessed
4. **Notify** community via GitHub Discussions
5. **Review** all their contributions

### If an Owner is compromised:

1. **Other Owner(s)** remove compromised owner
2. **GitHub Support** contacted if only owner
3. **All secrets rotated** (Railway tokens, bot token)
4. **Repository transferred** if necessary
5. **Community notified** publicly

### If ALL maintainers are compromised:

1. **Community forks** repository
2. **New maintainers** establish from fork
3. **Original repository** marked as compromised
4. **Users directed** to trusted fork
5. **No user data is lost** (not in repository)

---

## Succession Planning

### If maintainers become inactive:

| Duration | Action |
|----------|--------|
| 30 days | Other maintainers continue |
| 90 days | Recruit new maintainers publicly |
| 180 days | Transfer to trusted organization |
| 365 days | Archive with clear notice |

### Succession Criteria

New maintainers must:
- [ ] Have public contribution history
- [ ] Be vouched by existing maintainer
- [ ] Pass security review
- [ ] Agree to governance model
- [ ] Sign commits with verified GPG key

---

## Dispute Resolution

1. **Technical disputes**: Resolved by consensus, or security team decides
2. **Security disputes**: Security team has final say
3. **Governance disputes**: Resolved by owner vote
4. **Unresolvable disputes**: Fork is always an option

---

## Public Oversight

The community can:

- ✅ View all code changes
- ✅ Comment on all PRs
- ✅ Report security issues privately
- ✅ Fork at any time
- ✅ Audit commit history
- ✅ Verify signed commits
- ✅ Run their own instance

The community cannot:

- ❌ Access production secrets
- ❌ Access user data (doesn't exist in repo)
- ❌ Force merge without approval
- ❌ Change repository settings

---

## Governance Amendments

Changes to this governance model require:

1. Public PR with 30-day comment period
2. Approval from ALL active owners
3. Approval from majority of maintainers
4. No unresolved security objections

---

*This governance model is designed to ensure that no single individual—including the original creator—can unilaterally compromise user safety.*
