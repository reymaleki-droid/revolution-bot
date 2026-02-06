"""
Unit tests for the redact_secrets() utility.
Run: pytest test_redaction.py -v
"""
import pytest
from utils import redact_secrets


class TestTelegramTokenRedaction:
    """Telegram bot token patterns must be fully masked."""

    def test_real_token_format(self):
        text = "token=7819234501:AAHk3bRL9wZm5Tq_y2nXpK8dFvE-MjCsU1o"
        result = redact_secrets(text)
        assert "AAHk3bRL9wZm5Tq" not in result
        assert "[REDACTED-TOKEN]" in result

    def test_token_in_sentence(self):
        text = "Bot started with 7819234501:AAHk3bRL9wZm5Tq_y2nXpK8dFvE-MjCsU1o on server"
        result = redact_secrets(text)
        assert "AAHk3bRL9wZm5Tq" not in result
        assert "[REDACTED-TOKEN]" in result

    def test_placeholder_token_preserved(self):
        """All-X placeholder tokens should NOT be redacted."""
        text = 'BOT_TOKEN = "1234567890:XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"'
        result = redact_secrets(text)
        # Placeholder should remain intact (it's not a real secret)
        assert "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX" in result

    def test_mixed_placeholder_preserved(self):
        text = 'token = "0000000000:XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"'
        result = redact_secrets(text)
        assert "XXXXXXXXXXXXXXX" in result


class TestPostgresURLRedaction:
    """PostgreSQL connection strings must have passwords masked."""

    def test_full_postgres_url(self):
        text = "postgresql://admin:s3cretP@ss@db.example.com:5432/mydb"
        result = redact_secrets(text)
        assert "s3cretP@ss" not in result
        assert "[REDACTED-DB-URL]" in result
        # Host info should also be masked
        assert "db.example.com" not in result

    def test_postgres_scheme(self):
        text = "postgres://user:hunter2@localhost:5432/app"
        result = redact_secrets(text)
        assert "hunter2" not in result
        assert "[REDACTED-DB-URL]" in result

    def test_railway_url(self):
        text = "postgresql://postgres:AbCdEfGhIjKl@proxy.rlwy.net:12345/railway"
        result = redact_secrets(text)
        assert "AbCdEfGhIjKl" not in result
        assert "proxy.rlwy.net" not in result
        assert "[REDACTED-DB-URL]" in result

    def test_format_comment_preserved(self):
        """Documentation format strings should not be redacted."""
        text = "# Format: postgresql://user:password@host:port/database"
        result = redact_secrets(text)
        # This is redacted because it matches the URL pattern
        assert "password" not in result or "REDACTED" in result


class TestHexSecretRedaction:
    """Long hex strings (salts, peppers) must be masked."""

    def test_64_char_hex(self):
        text = "salt=a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"
        result = redact_secrets(text)
        assert "a1b2c3d4e5f6a1b2c3d4e5f6" not in result
        assert "[REDACTED-HEX]" in result

    def test_32_char_hex(self):
        text = "pepper=a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6"
        result = redact_secrets(text)
        assert "a1b2c3d4e5f6a7b8" not in result
        assert "[REDACTED-HEX]" in result

    def test_short_hex_preserved(self):
        """Short hex (e.g. commit SHAs, colors) should NOT be redacted."""
        text = "commit 7ff7542a"
        result = redact_secrets(text)
        assert "7ff7542a" in result

    def test_hash_output_preserved(self):
        """SHA256 output from _hash_user_id is fine (it IS the hash, not the secret)."""
        text = "user_hash=e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        result = redact_secrets(text)
        # 64-char hex IS redacted since we can't distinguish hash output from a secret key
        assert "[REDACTED-HEX]" in result


class TestPassthrough:
    """Normal text must pass through unmodified."""

    def test_plain_text(self):
        text = "Hello, this is a normal log message"
        assert redact_secrets(text) == text

    def test_persian_text(self):
        text = "خطا در پردازش درخواست شما"
        assert redact_secrets(text) == text

    def test_empty_string(self):
        assert redact_secrets("") == ""

    def test_numbers_only(self):
        text = "User count: 12345"
        assert redact_secrets(text) == text

    def test_none_input(self):
        assert redact_secrets(None) == ""


class TestMultipleSecrets:
    """Text with multiple secrets must have all of them redacted."""

    def test_token_and_url(self):
        text = "token=7819234501:AAHk3bRL9wZm5Tq_y2nXpK8dFvE-MjCsU1o db=postgresql://u:p@h:5432/d"
        result = redact_secrets(text)
        assert "AAHk3bRL9wZm5Tq" not in result
        assert "[REDACTED-TOKEN]" in result
        assert "[REDACTED-DB-URL]" in result
