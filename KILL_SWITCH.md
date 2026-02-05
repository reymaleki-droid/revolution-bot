# Emergency Kill-Switch Procedures

**Purpose**: Immediate response protocols for security incidents  
**Audience**: Maintainers and trusted community members  
**Principle**: Speed over perfection in emergencies  

---

## ⚠️ INCIDENT CATEGORIES

| Category | Severity | Response Time |
|----------|----------|---------------|
| **BOT COMPROMISE** | CRITICAL | < 5 minutes |
| **TOKEN LEAK** | CRITICAL | < 5 minutes |
| **CI COMPROMISE** | HIGH | < 30 minutes |
| **MAINTAINER COMPROMISE** | HIGH | < 1 hour |
| **DEPENDENCY VULNERABILITY** | MEDIUM | < 24 hours |

---

## 🔴 SCENARIO 1: BOT COMPROMISE

**Signs**: Bot sending unauthorized messages, accessing data unexpectedly, behaving erratically

### Immediate Actions (< 5 minutes)

```
STEP 1: STOP THE BOT
────────────────────
Railway Dashboard → Select Project → Deployments → 
Click "..." → "Remove Deployment"

OR via CLI:
railway down
```

```
STEP 2: REVOKE BOT TOKEN
────────────────────────
Telegram → @BotFather → /mybots → Select bot → 
"API Token" → "Revoke current token"

⚠️ This IMMEDIATELY disables the bot
```

```
STEP 3: ROTATE ALL SECRETS
──────────────────────────
Railway Dashboard → Variables → Delete and recreate:
- BOT_TOKEN (new from BotFather)
- HASH_PEPPER (new 64-char hex)
- USER_HASH_SALT (new 64-char hex)

Generate new secrets:
python -c "import secrets; print(secrets.token_hex(32))"
```

### Post-Incident (< 1 hour)

- [ ] Assess what data could have been accessed
- [ ] Check Railway logs for suspicious activity
- [ ] Review recent commits and merges
- [ ] Post public notice (see Communication Plan)
- [ ] Document incident in INCIDENTS.md

---

## 🔴 SCENARIO 2: TOKEN LEAK

**Signs**: Token found in public code, logs, or external report

### Immediate Actions (< 5 minutes)

```
STEP 1: REVOKE IMMEDIATELY
──────────────────────────
Do NOT wait to assess. Revoke first.

Telegram → @BotFather → /mybots → Select bot → 
"API Token" → "Revoke current token"
```

```
STEP 2: SEARCH FOR EXPOSURE
───────────────────────────
GitHub: Search repository for token pattern
Logs: Check Railway logs for token
History: git log -p | grep -i "token"
```

```
STEP 3: CLEAN HISTORY (if in git)
─────────────────────────────────
If token is in git history:

1. Use BFG Repo-Cleaner or git filter-branch
2. Force push cleaned history
3. Notify all forks to re-clone
4. GitHub: Contact support to clear caches
```

```
STEP 4: GENERATE NEW TOKEN
──────────────────────────
@BotFather → /mybots → Select bot → "API Token"
Update in Railway: Variables → BOT_TOKEN
```

### Post-Incident

- [ ] Determine how leak occurred
- [ ] Add prevention (pre-commit hooks, CI checks)
- [ ] Document in INCIDENTS.md

---

## 🟠 SCENARIO 3: CI COMPROMISE

**Signs**: Unexpected CI behavior, unauthorized actions, modified workflows

### Immediate Actions (< 30 minutes)

```
STEP 1: DISABLE GITHUB ACTIONS
──────────────────────────────
Settings → Actions → General → 
"Disable Actions" 

OR

Delete/disable the compromised workflow
```

```
STEP 2: REVOKE GITHUB TOKENS
────────────────────────────
Settings → Developer settings → Personal access tokens
Revoke any tokens that CI might have used
```

```
STEP 3: AUDIT RECENT RUNS
─────────────────────────
Actions tab → Review all recent workflow runs
Look for unexpected commands or outputs
```

```
STEP 4: REVIEW WORKFLOW FILES
─────────────────────────────
Check .github/workflows/*.yml for modifications
Compare against known-good versions
```

### Post-Incident

- [ ] Restore workflows from known-good backup
- [ ] Pin all action versions to specific SHAs
- [ ] Add workflow change notifications
- [ ] Document in INCIDENTS.md

---

## 🟠 SCENARIO 4: MAINTAINER COMPROMISE

**Signs**: Unauthorized merges, suspicious commits, account takeover

### Immediate Actions (< 1 hour)

```
STEP 1: REMOVE ACCESS
─────────────────────
Settings → Collaborators and teams → 
Remove compromised account

Settings → Moderation → Block user (if needed)
```

```
STEP 2: AUDIT THEIR ACTIONS
───────────────────────────
Settings → Security → Audit log
Filter by compromised user
Review all recent actions
```

```
STEP 3: REVERT SUSPICIOUS MERGES
────────────────────────────────
Identify suspicious commits:
git log --author="compromised@email.com"

Revert if necessary:
git revert <commit-sha>
```

```
STEP 4: ROTATE SECRETS (if they had access)
───────────────────────────────────────────
If maintainer had ANY production access:
- Rotate BOT_TOKEN
- Rotate HASH_PEPPER
- Rotate USER_HASH_SALT
- Rotate DATABASE_URL password
```

### Post-Incident

- [ ] Notify community
- [ ] Review all their historical contributions
- [ ] Update governance if needed
- [ ] Document in INCIDENTS.md

---

## 🟡 SCENARIO 5: DEPENDENCY VULNERABILITY

**Signs**: Dependabot alert, CVE announcement, security advisory

### Actions (< 24 hours)

```
STEP 1: ASSESS SEVERITY
───────────────────────
Read the CVE/advisory
Determine if it affects our usage
Check if exploit exists in the wild
```

```
STEP 2: UPDATE DEPENDENCY
─────────────────────────
Update requirements.txt
Test locally
Create PR with security label
Fast-track review (security team)
```

```
STEP 3: DEPLOY
──────────────
Merge PR (still requires 2 approvals)
Railway auto-deploys from main
```

---

## 📢 COMMUNICATION PLAN

### Template: Incident Notification

```markdown
## ⚠️ Security Incident Notice

**Date**: [DATE]
**Severity**: [CRITICAL/HIGH/MEDIUM]
**Status**: [INVESTIGATING/CONTAINED/RESOLVED]

### What Happened
[Brief description without sensitive details]

### User Impact
[What users need to know]

### What We Did
[Actions taken]

### What Users Should Do
[Any required user actions]

### Timeline
- [TIME]: Incident detected
- [TIME]: [Action taken]
- [TIME]: [Action taken]
- [TIME]: Incident resolved

### Transparency Note
[What we can/cannot disclose and why]
```

### Communication Channels

| Audience | Channel | Timing |
|----------|---------|--------|
| Maintainers | Private signal group | Immediately |
| Community | GitHub Discussions | After containment |
| Users | Bot announcement | After resolution |
| Public | README banner | If ongoing |

---

## 📋 INCIDENT CHECKLIST

Use this checklist for any incident:

### During Incident
- [ ] Identify incident category
- [ ] Execute immediate actions
- [ ] Document timeline as you go
- [ ] Notify other maintainers
- [ ] Avoid public disclosure until contained

### After Containment
- [ ] Complete post-incident actions
- [ ] Write incident report
- [ ] Identify root cause
- [ ] Implement prevention
- [ ] Public communication

### Post-Incident Review
- [ ] What went wrong?
- [ ] What went right?
- [ ] What could be faster?
- [ ] What process changes needed?
- [ ] Update this document if needed

---

## 🔐 SECRET ROTATION QUICK REFERENCE

### BOT_TOKEN
```
1. @BotFather → /mybots → Select bot → API Token → Revoke
2. Copy new token
3. Railway → Variables → BOT_TOKEN → Update
4. Redeploy
```

### HASH_PEPPER / USER_HASH_SALT
```
1. Generate: python -c "import secrets; print(secrets.token_hex(32))"
2. Railway → Variables → Update value
3. Redeploy

⚠️ WARNING: Changing pepper/salt invalidates existing user hashes
⚠️ All users will appear as "new" to the database
⚠️ Only rotate if compromised
```

### DATABASE_URL
```
1. Railway → Postgres service → Settings → Reset password
2. Copy new connection string
3. Railway → Bot service → Variables → DATABASE_URL → Update
4. Redeploy
```

---

## 📍 EMERGENCY CONTACTS

| Resource | Location |
|----------|----------|
| Railway Dashboard | https://railway.app/dashboard |
| BotFather | https://t.me/BotFather |
| GitHub Security | security@github.com |
| Telegram Support | https://telegram.org/support |

---

## 💡 REMEMBER

1. **Speed over perfection**: Revoke first, investigate later
2. **Assume the worst**: If token might be leaked, it IS leaked
3. **Document everything**: Timeline is critical for post-mortem
4. **Communicate clearly**: Users prefer honesty over silence
5. **Learn and improve**: Every incident improves security

---

*This document should be reviewed and updated after every incident.*
