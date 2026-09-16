"""User ORM row <-> domain model."""

from talentscout.adapters.db.orm import UserRow
from talentscout.constants.auth import Role
from talentscout.domain.user import User


def to_row(user: User) -> UserRow:
    return UserRow(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        password_hash=user.password_hash,
        role=user.role.value,
        is_active=user.is_active,
        created_at=user.created_at,
    )


def to_domain(row: UserRow) -> User:
    return User(
        id=row.id,
        email=row.email,
        full_name=row.full_name,
        password_hash=row.password_hash,
        role=Role(row.role),
        is_active=row.is_active,
        created_at=row.created_at,
    )
