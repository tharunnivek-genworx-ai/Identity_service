"""Seed or update a local/test IT admin account."""

import asyncio
import uuid

from sqlalchemy import select

from src.api.data.models.postgres.Identity_models import mentors, trainees
from src.api.data.clients.postgres.database import SessionLocal
from src.api.data.models.postgres.Identity_models import departments  # noqa: F401
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
                itadminid=ADMIN_ID,
                email=ADMIN_EMAIL,
                passwordhash=hash_password(ADMIN_PASSWORD),
                fullname=ADMIN_FULLNAME,
                phone=ADMIN_PHONE,
                isactive=True,
                createdat=utc_now(),
                updatedat=utc_now(),
            )
            session.add(admin)
        else:
            admin.passwordhash = hash_password(ADMIN_PASSWORD)
            admin.fullname = ADMIN_FULLNAME
            admin.phone = ADMIN_PHONE
            admin.isactive = True
            admin.deletedat = None
            admin.updatedat = utc_now()

        await session.commit()
        print(f"Seeded IT admin: {ADMIN_EMAIL}")


if __name__ == "__main__":
    asyncio.run(seed_it_admin())
