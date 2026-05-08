"""Family service layer — invite codes, membership, listings."""
from __future__ import annotations

import base64
import secrets
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1._errors import http_error
from app.models import Family, FamilyInvite, FamilyMember, User


def generate_invite_code() -> str:
    """Return an 8-char base32 invite code (5 bytes → 8 chars, no padding)."""
    raw = secrets.token_bytes(5)
    return base64.b32encode(raw).decode("ascii").rstrip("=")


async def create_family_with_owner(
    session: AsyncSession, user: User, name: str
) -> Family:
    """Create Family + owner FamilyMember row in a single transaction."""
    now = datetime.now(UTC)
    fam = Family(id=uuid.uuid4(), name=name, owner_id=user.id, created_at=now)
    session.add(fam)
    session.add(
        FamilyMember(family_id=fam.id, user_id=user.id, role="owner", joined_at=now)
    )
    await session.commit()
    await session.refresh(fam)
    return fam


async def list_my_families(session: AsyncSession, user: User) -> list[dict]:
    """Return ``[{id, name, role, member_count}]`` for the current user (D4)."""
    member_count = func.count(FamilyMember.user_id).label("member_count")

    # Subquery: families the user belongs to with their role
    my_membership = (
        select(FamilyMember.family_id, FamilyMember.role)
        .where(FamilyMember.user_id == user.id)
        .subquery()
    )

    stmt = (
        select(
            Family.id,
            Family.name,
            my_membership.c.role,
            member_count,
        )
        .join(my_membership, my_membership.c.family_id == Family.id)
        .join(FamilyMember, FamilyMember.family_id == Family.id)
        .group_by(Family.id, Family.name, my_membership.c.role)
        .order_by(Family.name)
    )
    rows = (await session.execute(stmt)).all()
    return [
        {
            "id": str(fid),
            "name": fname,
            "role": role,
            "member_count": int(count),
        }
        for fid, fname, role, count in rows
    ]


async def issue_invite(
    session: AsyncSession, family: Family, ttl_hours: int, issuer: User | None = None
) -> tuple[str, datetime]:
    """Generate a fresh invite code, persist new ``family_invite`` row, return (code, expires_at).

    V9: family_invite 테이블에 INSERT (1:N). 같은 family 가 여러 invite 동시 발급 가능.
    Retries once on rare uniqueness collisions (D5).
    """
    expires_at = datetime.now(UTC) + timedelta(hours=ttl_hours)
    issuer_id = issuer.id if issuer is not None else family.owner_id
    for _ in range(2):
        code = generate_invite_code()
        invite = FamilyInvite(
            id=uuid.uuid4(),
            family_id=family.id,
            code=code,
            expires_at=expires_at,
            created_by=issuer_id,
        )
        session.add(invite)
        try:
            await session.commit()
            return code, expires_at
        except IntegrityError:
            await session.rollback()
            continue
    raise http_error(500, "INTERNAL", "failed to generate unique invite code")


async def join_by_code(
    session: AsyncSession, user: User, invite_code: str
) -> Family:
    """Resolve invite_code → join family as ``member``.

    V9: family_invite.code 로 lookup. expires_at 검증.
    Raises 404 NOT_FOUND, 410 INVITE_EXPIRED, 409 ALREADY_MEMBER.
    """
    invite = (
        await session.execute(
            select(FamilyInvite).where(FamilyInvite.code == invite_code)
        )
    ).scalar_one_or_none()
    if invite is None:
        raise http_error(404, "NOT_FOUND", "invite code not found")

    now = datetime.now(UTC)
    if invite.expires_at is None or invite.expires_at < now:
        raise http_error(410, "INVITE_EXPIRED", "invite code expired")

    fam = await session.get(Family, invite.family_id)
    if fam is None:
        raise http_error(404, "NOT_FOUND", "family not found")

    existing = (
        await session.execute(
            select(FamilyMember).where(
                FamilyMember.family_id == fam.id, FamilyMember.user_id == user.id
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise http_error(409, "ALREADY_MEMBER", "already a member of this family")

    session.add(
        FamilyMember(family_id=fam.id, user_id=user.id, role="member", joined_at=now)
    )
    await session.commit()
    return fam


async def list_members(session: AsyncSession, family: Family) -> list[dict]:
    stmt = (
        select(FamilyMember.user_id, User.name, FamilyMember.role, FamilyMember.joined_at)
        .join(User, User.id == FamilyMember.user_id)
        .where(FamilyMember.family_id == family.id)
        .order_by(FamilyMember.joined_at)
    )
    rows = (await session.execute(stmt)).all()
    return [
        {
            "user_id": str(uid),
            "name": name,
            "role": role,
            "joined_at": joined_at.isoformat(),
        }
        for uid, name, role, joined_at in rows
    ]
