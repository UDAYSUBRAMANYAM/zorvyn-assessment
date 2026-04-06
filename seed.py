import asyncio
import random
from datetime import date, timedelta

from sqlalchemy import select

from app.core.database import AsyncSessionLocal, init_db
from app.models.financial_record import FinancialRecord, RecordType
from app.models.user import User, UserRole, UserStatus
from app.services.auth_service import hash_password


CATEGORIES = {
    RecordType.income: ["salary", "freelance", "investment", "bonus", "rental"],
    RecordType.expense: ["food", "utilities", "transport", "healthcare", "entertainment", "rent"],
}


async def run_seed():
    await init_db()

    async with AsyncSessionLocal() as db:
        # ✅ Prevent duplicate seeding
        result = await db.execute(select(User).limit(1))
        if result.scalars().first():
            print("⚠️ Data already exists, skipping seed")
            return

        # ── Users ─────────────────────────────
        users_data = [
            ("admin@example.com", "Admin User", "Admin@123456", UserRole.admin),
            ("analyst@example.com", "Analyst User", "Analyst@123", UserRole.analyst),
            ("viewer@example.com", "Viewer User", "Viewer@1234", UserRole.viewer),
        ]

        admin_id = None

        for email, name, pwd, role in users_data:
            user = User(
                email=email,
                full_name=name,
                hashed_password=hash_password(pwd),
                role=role,
                status=UserStatus.active,
            )
            db.add(user)
            await db.flush()

            if role == UserRole.admin:
                admin_id = user.id

        await db.commit()
        print("✅ Users seeded")

        # ── Financial records ─────────────────
        base_date = date(2024, 1, 1)

        for _ in range(30):
            rtype = random.choice(list(RecordType))
            category = random.choice(CATEGORIES[rtype])
            amount = round(random.uniform(100, 15000), 2)
            record_date = base_date + timedelta(days=random.randint(0, 180))

            record = FinancialRecord(
                amount=amount,
                type=rtype,
                category=category,
                record_date=record_date,
                description=f"Demo {rtype.value} - {category}",
                created_by=admin_id,
            )
            db.add(record)

        await db.commit()
        print("✅ Financial records seeded")

    print("🎉 Seeding complete")