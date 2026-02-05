# Threat Model

This document describes the security threats this project is designed to protect against, and explains why users remain safe even under adversarial conditions.

## Target Users

This bot serves **high-risk users**:
- Activists and human rights defenders
- Journalists in restrictive regions
- Political organizers
- Diaspora communities

**Threat assumption**: State-level adversaries with significant resources.

---

## Attack Scenarios

### 1. Repository Compromise

**Scenario**: An attacker gains write access to the GitHub repository.

| Attack Vector | Impact | Mitigation |
|---------------|--------|------------|
| Inject malicious code | HIGH | Branch protection, required reviews, signed commits |
| Steal secrets from code | NONE | No secrets in repository |
| Access user data | NONE | No user data in repository |
| Backdoor CI/CD | MEDIUM | GitHub Actions security scanning, pinned dependencies |

**Why users remain safe**:
- No secrets exist in the repository to steal
- User data is never stored in code
- Malicious code would be caught by required reviews
- CI automatically scans all PRs for secrets

**Residual risk**: Sophisticated supply chain attack could inject code if reviews are bypassed.

---

### 2. Database Breach

**Scenario**: An attacker obtains a full copy of the PostgreSQL database.

| Data Type | Stored? | Recoverable? | Impact |
|-----------|---------|--------------|--------|
| User IDs | NO (hashed) | NO | NONE |
| Usernames | NO | N/A | NONE |
| Names | NO | N/A | NONE |
| Phone numbers | NO | N/A | NONE |
| Messages | NO | N/A | NONE |
| Points/Ranks | YES | YES | LOW |
| Timestamps | YES | YES | LOW |

**Why users remain safe**:
```
user_hash = HMAC-SHA256(HASH_PEPPER, user_id || USER_HASH_SALT)
```

To reverse this hash, an attacker would need:
1. The HASH_PEPPER (not in database, only in environment)
2. The USER_HASH_SALT (not in database, only in environment)
3. Brute force all possible Telegram user IDs (~10^10)
4. Compare each hash against the database

**Mathematical analysis**:
- HMAC-SHA256 provides 128-bit security against collision attacks
- Pepper + salt makes rainbow tables useless
- Even with pepper, brute forcing 10 billion IDs takes ~years on modern hardware
- AND the attacker gains nothing useful (just a Telegram user ID)

**Residual risk**: If HASH_PEPPER is also compromised AND attacker has specific target user IDs, they could verify presence in database.

---

### 3. Environment/Server Compromise

**Scenario**: An attacker gains access to the Railway hosting environment.

| Asset | Location | Impact if Compromised |
|-------|----------|----------------------|
| BOT_TOKEN | Environment | Can impersonate bot |
| DATABASE_URL | Environment | Can read hashed data |
| HASH_PEPPER | Environment | Can verify user presence |
| USER_HASH_SALT | Environment | Required with pepper |
| Running memory | Server | Can see current requests |

**Why users remain safe**:
- Even with all secrets, attacker only gets hashed user IDs
- No message content is ever stored or logged
- No file content is ever stored
- Point/rank data is non-sensitive

**Attacker capabilities gained**:
1. Impersonate the bot (send messages as bot)
2. Verify if a specific user ID is in the database
3. See current requests in memory (temporary)

**Attacker CANNOT**:
1. Recover usernames or display names
2. Access historical messages
3. Access submitted media
4. Identify users without already knowing their IDs
5. See any PII whatsoever

**Residual risk**: Live impersonation of bot; verification of known user ID presence.

---

### 4. Insider Threat (Malicious Admin)

**Scenario**: A bot administrator acts maliciously.

| Admin Capability | Can Do | Cannot Do |
|------------------|--------|-----------|
| View aggregate stats | ✅ | View individual user data |
| Approve/reject submissions | ✅ | See who submitted (hashed) |
| Access /stats command | ✅ | Export user identities |
| Read logs | ✅ | Find user IDs in logs |

**Why users remain safe**:
- Admin commands use `(identity protected)` logging
- No admin function can de-anonymize users
- Submission tokens are random, not user-derived
- Admin sees points/ranks but not who owns them

**Residual risk**: Admin could correlate timing of submissions with external observations.

---

### 5. CI/CD Breach

**Scenario**: GitHub Actions workflow is compromised.

| Attack Vector | Impact | Mitigation |
|---------------|--------|------------|
| Steal GITHUB_TOKEN | LOW | Limited permissions, read-only |
| Inject into build | MEDIUM | Pinned actions, security scanning |
| Access secrets | LOW | No production secrets in CI |
| Modify releases | HIGH | Required reviews, branch protection |

**Why users remain safe**:
- CI has no access to production secrets
- CI has no access to database
- CI cannot access user data

**Residual risk**: Compromised CI could inject malicious code into releases.

---

### 6. Dependency/Supply Chain Attack

**Scenario**: A Python package dependency is compromised.

| Protection | Implementation |
|------------|----------------|
| Dependabot | Automated vulnerability alerts |
| Safety scan | CI checks for known vulnerabilities |
| Pinned versions | requirements.txt pins exact versions |
| Limited deps | Minimal dependency surface |

**Why users remain safe**:
- Compromised dependency would need to execute in production
- Even then, it can only access hashed data
- No PII exists to exfiltrate

**Residual risk**: Sophisticated dependency attack could exfiltrate data in transit.

---

## Data Recovery Analysis

### What is mathematically unrecoverable

| Data | Why Unrecoverable |
|------|-------------------|
| User ID → Hash | HMAC is one-way; requires pepper+salt |
| Hash → User ID | HMAC-SHA256 is computationally irreversible |
| Username | Never stored, cannot be recovered |
| Display name | Never stored, cannot be recovered |
| Message content | Never stored, cannot be recovered |
| Submitted files | Never stored, cannot be recovered |

### What CAN be recovered (with full access)

| Data | Condition |
|------|-----------|
| Points/ranks | Direct database access |
| Action timestamps | Direct database access |
| Aggregate statistics | Direct database access |
| User presence (yes/no) | Pepper + salt + known user ID |

---

## What Admins CANNOT See

Even with full administrative access:

1. ❌ Which Telegram user earned specific points
2. ❌ Who submitted which content
3. ❌ User's Telegram username or display name
4. ❌ User's phone number
5. ❌ Content of any messages
6. ❌ Submitted photos or videos
7. ❌ User's IP address or location
8. ❌ User's device information

---

## What the Bot CANNOT Access

The bot code has these **inherent limitations**:

1. **Cannot store PII**: Database schema has no PII columns
2. **Cannot log PII**: Logging is sanitized
3. **Cannot reverse hashes**: HMAC is mathematically one-way
4. **Cannot access without env**: Fail-closed on missing secrets
5. **Cannot persist files**: All files are temporary

---

## Residual Risks

These risks remain even with all protections:

| Risk | Likelihood | Impact | Notes |
|------|------------|--------|-------|
| Live server compromise | LOW | MEDIUM | Can see current requests |
| Timing correlation | LOW | LOW | External observation required |
| Social engineering | MEDIUM | VARIES | Human factor |
| Zero-day in dependencies | LOW | VARIES | Mitigated by scanning |
| Sophisticated state actor | LOW | MEDIUM | Beyond threat model scope |

---

## Conclusion

This system is designed with **defense in depth**:

1. **Layer 1**: No secrets in code
2. **Layer 2**: No PII in database
3. **Layer 3**: Irreversible hashing
4. **Layer 4**: Automated security scanning
5. **Layer 5**: Human review requirements
6. **Layer 6**: Minimal data collection

**Even in a worst-case scenario** (full database + environment compromise), an attacker:
- Cannot identify users without already knowing their IDs
- Cannot recover any usernames, names, or contact info
- Cannot access any historical messages or files
- Can only verify presence of specific known users

This provides meaningful protection for high-risk users against sophisticated adversaries.
