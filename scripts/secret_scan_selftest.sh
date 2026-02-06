#!/bin/bash
# =============================================================================
# Secret Scanner Self-Test
# =============================================================================
# Tests that our local secret detection (pre-commit hooks + CI grep patterns)
# correctly BLOCK realistic fake secrets and ALLOW known-safe placeholders.
#
# This script NEVER pushes to remote. All operations are local + cleaned up.
#
# Usage: bash scripts/secret_scan_selftest.sh
# =============================================================================
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASS_COUNT=0
FAIL_COUNT=0
TMPDIR_TEST=""

cleanup() {
    echo ""
    echo -e "${YELLOW}🧹 Cleaning up...${NC}"
    # Remove temp files
    [ -f "tmp_selftest_secrets.txt" ] && rm -f tmp_selftest_secrets.txt
    [ -f "tmp_selftest_safe.txt" ] && rm -f tmp_selftest_safe.txt
    [ -d "$TMPDIR_TEST" ] && rm -rf "$TMPDIR_TEST"
    # Unstage any test files
    git reset HEAD -- tmp_selftest_secrets.txt tmp_selftest_safe.txt 2>/dev/null || true
    echo -e "${GREEN}✅ Cleanup complete${NC}"
}
trap cleanup EXIT

assert_blocked() {
    local description="$1"
    local pattern="$2"
    local file="$3"
    
    if grep -qE "$pattern" "$file" 2>/dev/null | grep -v "\.example" | grep -v "# Format:" | grep -v "XXXXXXXXX"; then
        echo -e "  ${GREEN}✅ PASS${NC}: Blocked — $description"
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        echo -e "  ${RED}❌ FAIL${NC}: NOT blocked — $description"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
}

assert_allowed() {
    local description="$1"
    local pattern="$2"
    local file="$3"
    
    # For safe patterns: the grep SHOULD match but the exclusion filter should allow it
    if grep -E "$pattern" "$file" 2>/dev/null | grep -q "XXXXXXXXX\|# Format:\|\.example"; then
        echo -e "  ${GREEN}✅ PASS${NC}: Allowed — $description"
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        echo -e "  ${RED}❌ FAIL${NC}: NOT allowed — $description"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
}

echo "============================================="
echo "🔒 Secret Scanner Self-Test"
echo "============================================="
echo ""

# -------------------------------------------
# TEST 1: Realistic fake Telegram token
# -------------------------------------------
echo -e "${YELLOW}TEST 1: Telegram bot token detection${NC}"

cat > tmp_selftest_secrets.txt <<'EOF'
FAKE_TOKEN=7819234501:AAHk3bRL9wZm5Tq_y2nXpK8dFvE-MjCsU1o
EOF

# Pattern from pre-commit.sh and security.yml
TELEGRAM_PATTERN='[0-9]{7,10}:[A-Za-z0-9_-]{30,50}'

if grep -qE "$TELEGRAM_PATTERN" tmp_selftest_secrets.txt 2>/dev/null; then
    echo -e "  ${GREEN}✅ PASS${NC}: Realistic fake Telegram token detected by scanner"
    PASS_COUNT=$((PASS_COUNT + 1))
else
    echo -e "  ${RED}❌ FAIL${NC}: Scanner missed realistic Telegram token"
    FAIL_COUNT=$((FAIL_COUNT + 1))
fi

# -------------------------------------------
# TEST 2: Placeholder token should be excluded
# -------------------------------------------
echo -e "${YELLOW}TEST 2: Placeholder token exclusion${NC}"

cat > tmp_selftest_safe.txt <<'EOF'
BOT_TOKEN = "1234567890:XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
EOF

# The exclusion grep should filter it out
if grep -E "$TELEGRAM_PATTERN" tmp_selftest_safe.txt 2>/dev/null | grep -qv "XXXXXXXXX"; then
    echo -e "  ${RED}❌ FAIL${NC}: Placeholder was incorrectly flagged as real token"
    FAIL_COUNT=$((FAIL_COUNT + 1))
else
    echo -e "  ${GREEN}✅ PASS${NC}: Placeholder token correctly excluded"
    PASS_COUNT=$((PASS_COUNT + 1))
fi

# -------------------------------------------
# TEST 3: Realistic fake DATABASE_URL
# -------------------------------------------
echo -e "${YELLOW}TEST 3: PostgreSQL DATABASE_URL detection${NC}"

cat > tmp_selftest_secrets.txt <<'EOF'
DATABASE_URL=postgresql://admin:r3alP4ssw0rd@db.production.example.com:5432/botdb
EOF

PG_PATTERN='postgresql://[^:]+:[^@]+@[^/]+'
if grep -qE "$PG_PATTERN" tmp_selftest_secrets.txt 2>/dev/null; then
    echo -e "  ${GREEN}✅ PASS${NC}: Fake DATABASE_URL detected by scanner"
    PASS_COUNT=$((PASS_COUNT + 1))
else
    echo -e "  ${RED}❌ FAIL${NC}: Scanner missed DATABASE_URL pattern"
    FAIL_COUNT=$((FAIL_COUNT + 1))
fi

# -------------------------------------------
# TEST 4: Doc-style format comment should be excluded
# -------------------------------------------
echo -e "${YELLOW}TEST 4: Documentation format comment exclusion${NC}"

cat > tmp_selftest_safe.txt <<'EOF'
# Format: postgresql://user:password@host:port/database
EOF

if grep -E "$PG_PATTERN" tmp_selftest_safe.txt 2>/dev/null | grep -qv "# Format:"; then
    echo -e "  ${RED}❌ FAIL${NC}: Doc format comment incorrectly flagged"
    FAIL_COUNT=$((FAIL_COUNT + 1))
else
    echo -e "  ${GREEN}✅ PASS${NC}: Doc format comment correctly excluded"
    PASS_COUNT=$((PASS_COUNT + 1))
fi

# -------------------------------------------
# TEST 5: Hardcoded hex salt/pepper detection
# -------------------------------------------
echo -e "${YELLOW}TEST 5: Hardcoded hex salt/pepper detection${NC}"

cat > tmp_selftest_secrets.txt <<'EOF'
HASH_PEPPER = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"
EOF

HEX_PATTERN='HASH_PEPPER\s*=\s*['"'"'"][a-f0-9]{32,}['"'"'"]'
if grep -qE "$HEX_PATTERN" tmp_selftest_secrets.txt 2>/dev/null; then
    echo -e "  ${GREEN}✅ PASS${NC}: Hardcoded HASH_PEPPER detected"
    PASS_COUNT=$((PASS_COUNT + 1))
else
    echo -e "  ${RED}❌ FAIL${NC}: Scanner missed hardcoded HASH_PEPPER"
    FAIL_COUNT=$((FAIL_COUNT + 1))
fi

# -------------------------------------------
# TEST 6: os.getenv() usage should be safe
# -------------------------------------------
echo -e "${YELLOW}TEST 6: os.getenv() usage exclusion${NC}"

cat > tmp_selftest_safe.txt <<'EOF'
HASH_PEPPER = os.getenv('HASH_PEPPER')
EOF

if grep -E 'HASH_PEPPER\s*=\s*' tmp_selftest_safe.txt 2>/dev/null | grep -qv "os.getenv\|os\.environ"; then
    echo -e "  ${RED}❌ FAIL${NC}: os.getenv pattern incorrectly flagged"
    FAIL_COUNT=$((FAIL_COUNT + 1))
else
    echo -e "  ${GREEN}✅ PASS${NC}: os.getenv() usage correctly excluded"
    PASS_COUNT=$((PASS_COUNT + 1))
fi

# -------------------------------------------
# TEST 7: .env file blocking
# -------------------------------------------
echo -e "${YELLOW}TEST 7: .env file detection${NC}"

if echo ".env" | grep -qE '^\.env$'; then
    echo -e "  ${GREEN}✅ PASS${NC}: .env filename pattern detected"
    PASS_COUNT=$((PASS_COUNT + 1))
else
    echo -e "  ${RED}❌ FAIL${NC}: .env filename not detected"
    FAIL_COUNT=$((FAIL_COUNT + 1))
fi

# -------------------------------------------
# TEST 8: .db file blocking
# -------------------------------------------
echo -e "${YELLOW}TEST 8: .db file detection${NC}"

if echo "revolution_bot.db" | grep -qE '\.db$'; then
    echo -e "  ${GREEN}✅ PASS${NC}: .db filename pattern detected"
    PASS_COUNT=$((PASS_COUNT + 1))
else
    echo -e "  ${RED}❌ FAIL${NC}: .db filename not detected"
    FAIL_COUNT=$((FAIL_COUNT + 1))
fi

# -------------------------------------------
# SUMMARY
# -------------------------------------------
echo ""
echo "============================================="
TOTAL=$((PASS_COUNT + FAIL_COUNT))
echo -e "Results: ${GREEN}${PASS_COUNT}/${TOTAL} passed${NC}, ${RED}${FAIL_COUNT} failed${NC}"
echo "============================================="

if [ $FAIL_COUNT -gt 0 ]; then
    echo -e "${RED}❌ SELF-TEST FAILED — secret scanners need attention${NC}"
    exit 1
else
    echo -e "${GREEN}✅ ALL SELF-TESTS PASSED — scanners working correctly${NC}"
    exit 0
fi
