# Platform Hardening Complete

**Date**: February 2026  
**Scope**: GitHub repository hardening for public open-source release  
**Risk Context**: High-risk users (activists, journalists) in hostile environments  

---

## Executive Summary

> **"This project is designed to fail safely."**

Every protection layer assumes the previous layer has been compromised.  
No single individual—including the original creator—can unilaterally harm users.

---

## 1. Branch Protection Checklist

| Setting | Status | File |
|---------|--------|------|
| Require PR before merge | ✅ Documented | [BRANCH_PROTECTION.md](BRANCH_PROTECTION.md) |
| Require 2 approvals | ✅ Documented | [BRANCH_PROTECTION.md](BRANCH_PROTECTION.md) |
| Dismiss stale approvals | ✅ Documented | [BRANCH_PROTECTION.md](BRANCH_PROTECTION.md) |
| Require CI pass | ✅ Documented | [BRANCH_PROTECTION.md](BRANCH_PROTECTION.md) |
| Block force push | ✅ Documented | [BRANCH_PROTECTION.md](BRANCH_PROTECTION.md) |
| Block deletion | ✅ Documented | [BRANCH_PROTECTION.md](BRANCH_PROTECTION.md) |
| Require signed commits | ✅ Documented | [BRANCH_PROTECTION.md](BRANCH_PROTECTION.md) |
| CODEOWNERS | ✅ Created | [.github/CODEOWNERS](.github/CODEOWNERS) |

**Action Required**: Enable these settings in GitHub UI before going public.

---

## 2. Governance Summary

| Role | Can Merge | Can Approve | Can Change Settings | Can Access Production |
|------|-----------|-------------|---------------------|----------------------|
| Owner | ✅* | ✅ | ✅ (logged) | ❌ |
| Security Team | ✅* | ✅ | ❌ | ❌ |
| Maintainer | ✅* | ✅ | ❌ | ❌ |
| Reviewer | ❌ | ✅ | ❌ | ❌ |
| Contributor | ❌ | ❌ | ❌ | ❌ |

`*` Requires 2 approvals + CI pass + cannot be own PR

**Key Principle**: No one can merge alone. No one can bypass CI. No one can access production secrets from GitHub.

**Full Details**: [GOVERNANCE.md](GOVERNANCE.md)

---

## 3. Kill-Switch Summary

| Scenario | Response Time | Primary Action | Document |
|----------|---------------|----------------|----------|
| Bot Compromise | < 5 min | Revoke token via @BotFather | [KILL_SWITCH.md](KILL_SWITCH.md) |
| Token Leak | < 5 min | Revoke token, clean history | [KILL_SWITCH.md](KILL_SWITCH.md) |
| CI Compromise | < 30 min | Disable Actions, audit | [KILL_SWITCH.md](KILL_SWITCH.md) |
| Maintainer Compromise | < 1 hour | Remove access, audit, rotate | [KILL_SWITCH.md](KILL_SWITCH.md) |

**Full Procedures**: [KILL_SWITCH.md](KILL_SWITCH.md)

---

## 4. Trust Signals

| Signal | Location | Type |
|--------|----------|------|
| Security & Trust section | [README.md](README.md) | Visibility |
| "What we CANNOT do" | [README.md](README.md) | Guarantee |
| Transparency commitments | [README.md](README.md) | Promise |
| Trust signals table | [SECURITY.md](SECURITY.md) | Verification |
| Failure scenarios | [SECURITY.md](SECURITY.md) | Transparency |
| Threat model | [THREAT_MODEL.md](THREAT_MODEL.md) | Documentation |

---

## 5. Legal & Liability

| Document | Addition |
|----------|----------|
| [README.md](README.md) | Full legal section with guarantees/non-guarantees |
| [SECURITY.md](SECURITY.md) | Liability limitations |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Contributor agreement |

**Summary**:
- MIT License (no warranty)
- Contributors not liable for use
- Users responsible for their deployments
- No jurisdiction claims
- Fork rights guaranteed

---

## 6. Final Failure Analysis

### GitHub Compromised

| What Users Lose | What Users Keep |
|-----------------|-----------------|
| Trust in repo (temporary) | All their data (none stored) |
| Service (until fork) | Identity protection |
| | Fork rights |

### ALL Maintainers Compromised

| What Users Lose | What Users Keep |
|-----------------|-----------------|
| Trust in maintainers | All their data (none stored) |
| Service (until community fork) | Identity protection |
| | Full code history (public) |
| | Ability to verify/fork |

### CI Malicious

| What Users Lose | What Users Keep |
|-----------------|-----------------|
| Confidence in builds | All their data (CI has no access) |
| | Production secrets (not in CI) |
| | Ability to build locally |

### Database Breached

| What Users Lose | What Users Keep |
|-----------------|-----------------|
| Points/ranks (non-sensitive) | Identity (hashed, irreversible) |
| | Messages (never stored) |
| | Files (never persisted) |
| | Location (never collected) |

---

## Files Created for Platform Hardening

| File | Purpose |
|------|---------|
| [BRANCH_PROTECTION.md](BRANCH_PROTECTION.md) | GitHub settings checklist |
| [GOVERNANCE.md](GOVERNANCE.md) | Role permissions and limits |
| [KILL_SWITCH.md](KILL_SWITCH.md) | Emergency procedures |
| [.github/CODEOWNERS](.github/CODEOWNERS) | Required reviewers |

## Files Updated

| File | Changes |
|------|---------|
| [README.md](README.md) | Trust signals, legal section |
| [SECURITY.md](SECURITY.md) | Trust signals, failure analysis, liability |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Contributor liability agreement |

---

## Pre-Public Checklist

### GitHub Settings (Manual)

- [ ] Enable branch protection per [BRANCH_PROTECTION.md](BRANCH_PROTECTION.md)
- [ ] Create teams: `@helpiran-security-team`, `@helpiran-core-maintainers`
- [ ] Assign CODEOWNERS teams
- [ ] Enable secret scanning alerts
- [ ] Enable Dependabot alerts
- [ ] Enable security advisories
- [ ] Set repository to Public

### Verification

- [ ] Test: Direct push to main fails
- [ ] Test: PR without approval cannot merge
- [ ] Test: PR with failing CI cannot merge
- [ ] Test: Force push rejected
- [ ] Review: All CI workflows work

---

## Final Statement

---

### **This project is designed to fail safely.**

---

**Assumptions**:
- GitHub will be compromised
- Maintainers will be compromised
- CI will be malicious
- Database will be breached
- Dependencies will have vulnerabilities

**Guarantees Despite Failures**:
- User identities remain protected (mathematically)
- No PII can be leaked (doesn't exist)
- Fork rights preserved (MIT License)
- Audit trail public (git history)
- Community can continue (fork and go)

**Trust Model**:
- No trust in individuals
- No trust in platforms
- No trust in infrastructure
- Trust only in mathematics (HMAC-SHA256)
- Trust only in transparency (public code)

---

*Prepared for hostile review. Designed for worst-case. Built for activists.*
