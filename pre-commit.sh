#!/bin/bash
# Pre-commit hook to prevent accidental secret commits
# Install: cp pre-commit.sh .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit

echo "🔒 Running security checks..."

# Patterns that indicate secrets
PATTERNS=(
    "[0-9]{7,10}:[A-Za-z0-9_-]{30,50}"  # Telegram bot token
    "postgresql://[^'\"\s]+"            # PostgreSQL connection string
    "password\s*=\s*['\"][^'\"]+['\"]"  # Hardcoded passwords
    "HASH_PEPPER\s*=\s*['\"][a-f0-9]{32,}"  # Hardcoded pepper
    "USER_HASH_SALT\s*=\s*['\"][a-f0-9]{32,}"  # Hardcoded salt
)

# Files to check (staged files)
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(py|json|yml|yaml|md|txt|ini|cfg|toml)$')

if [ -z "$STAGED_FILES" ]; then
    echo "✅ No relevant files staged"
    exit 0
fi

FOUND_SECRETS=0

for pattern in "${PATTERNS[@]}"; do
    # Check each staged file
    for file in $STAGED_FILES; do
        if [ -f "$file" ]; then
            MATCHES=$(grep -nE "$pattern" "$file" 2>/dev/null | grep -v "\.example\|# Format:\|# Generate with:")
            if [ -n "$MATCHES" ]; then
                echo "❌ POTENTIAL SECRET in $file:"
                echo "$MATCHES"
                FOUND_SECRETS=1
            fi
        fi
    done
done

# Check for .env files being committed
ENV_FILES=$(git diff --cached --name-only | grep -E '^\.env$|^\.env\.[^e]')
if [ -n "$ENV_FILES" ]; then
    echo "❌ BLOCKED: Attempting to commit .env file(s):"
    echo "$ENV_FILES"
    FOUND_SECRETS=1
fi

# Check for database files
DB_FILES=$(git diff --cached --name-only | grep -E '\.db$|\.sqlite')
if [ -n "$DB_FILES" ]; then
    echo "❌ BLOCKED: Attempting to commit database file(s):"
    echo "$DB_FILES"
    FOUND_SECRETS=1
fi

# Check for salt files
SALT_FILES=$(git diff --cached --name-only | grep -E '\.salt$')
if [ -n "$SALT_FILES" ]; then
    echo "❌ BLOCKED: Attempting to commit salt file(s):"
    echo "$SALT_FILES"
    FOUND_SECRETS=1
fi

if [ $FOUND_SECRETS -eq 1 ]; then
    echo ""
    echo "🚫 COMMIT BLOCKED - Potential secrets detected!"
    echo "   Review the files above and remove any secrets."
    echo "   Use environment variables instead."
    echo ""
    echo "   To bypass (NOT RECOMMENDED): git commit --no-verify"
    exit 1
fi

echo "✅ Security checks passed"
exit 0
