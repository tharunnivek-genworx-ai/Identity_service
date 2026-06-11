"""Seed or update a local/test IT admin account."""

import asyncio
import uuid

from sqlalchemy import select

from src.api.data.clients.postgres.database import SessionLocal
from src.api.data.models.postgres.Identity_models import (
    departments,  # noqa: F401
)
from src.api.data.models.postgres.Identity_models.it_admin import ITAdmin
from src.api.utils.password import hash_password
from src.api.utils.time import utc_now

ADMIN_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
ADMIN_EMAIL = "tharunnivekdev@gmail.com"
ADMIN_PASSWORD = "Admin@123"
ADMIN_FULLNAME = "Tharun Nivek"
ADMIN_PHONE = "7010043099"


async def seed_it_admin() -> None:
    async with SessionLocal() as session:
        result = await session.execute(
            select(ITAdmin).where(ITAdmin.email == ADMIN_EMAIL)
        )
        admin = result.scalars().first()

        if admin is None:
            admin = ITAdmin(
                it_admin_id=ADMIN_ID,
                email=ADMIN_EMAIL,
                password_hash=hash_password(ADMIN_PASSWORD),
                full_name=ADMIN_FULLNAME,
                phone=ADMIN_PHONE,
                is_active=True,
                created_at=utc_now(),
                updated_at=utc_now(),
            )
            session.add(admin)
        else:
            admin.password_hash = hash_password(ADMIN_PASSWORD)
            admin.full_name = ADMIN_FULLNAME
            admin.phone = ADMIN_PHONE
            admin.is_active = True
            admin.deleted_at = None
            admin.updated_at = utc_now()

        await session.commit()
        print(f"Seeded IT admin: {ADMIN_EMAIL}")


if __name__ == "__main__":
    asyncio.run(seed_it_admin())
