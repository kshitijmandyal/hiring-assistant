"""bcrypt adapter satisfying the PasswordHasher protocol."""

from talentscout.adapters.security import passwords


class BcryptPasswordHasher:
    def hash(self, password: str) -> str:
        return passwords.hash_password(password)

    def verify(self, password: str, password_hash: str) -> bool:
        return passwords.verify_password(password, password_hash)
