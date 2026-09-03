"""Field-level encryption for secrets stored at rest (the token vault).

Values are transparently Fernet-encrypted on the way to the DB and decrypted
on the way out, so refresh/access tokens are never stored in plaintext.
"""

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.db import models


def _fernet() -> Fernet:
    key = settings.HUB_FIELD_ENCRYPTION_KEY
    if isinstance(key, str):
        key = key.encode()
    return Fernet(key)


class EncryptedTextField(models.TextField):
    """A TextField whose DB representation is Fernet ciphertext."""

    def get_prep_value(self, value):
        if value is None or value == '':
            return value
        return _fernet().encrypt(str(value).encode()).decode()

    def from_db_value(self, value, expression, connection):
        if value is None or value == '':
            return value
        try:
            return _fernet().decrypt(value.encode()).decode()
        except (InvalidToken, ValueError):
            # Value was stored unencrypted or with a different key.
            return value

    def to_python(self, value):
        return value
