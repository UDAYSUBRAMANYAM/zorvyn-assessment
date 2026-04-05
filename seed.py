"""
Seed script — populates the database with demo data.

Usage:
    python seed.py

Creates:
  - 1 Admin user  (admin@example.com / Admin@123456)
  - 1 Analyst     (analyst@example.com / Analyst@123)
  - 1 Viewer      (viewer@example.com / Viewer@1234)
  - 30 financial records spread across 6 months
"""
import asyncio
import random
from datetime import date, timedelta

from app.core.database import AsyncSessionLocal, init_db
from app.models.financial_record import FinancialRecord, RecordType
from app.models.user import User, UserRole, UserStatus
from app.services.auth_service import hash_password

CATEGORIES = {
    RecordType.income: ["salary", "freelance", "investment", "bonus", "rental"],
    RecordType.expense: ["food", "utilities", "transport", "healthcare", "entertainment", "rent"],
}


async def seed():
    await init_db()
    async with AsyncSessionLocal() as db:
        # ── Users ─────────────────────────────────────────────────────────────
        users_data = [
            ("admin@example.com",   "Admin User",    "Admin@123456",  UserRole.admin),
            ("analyst@example.com", "Analyst User",  "Analyst@123",   UserRole.analyst),
            ("viewer@example.com",  "Viewer User",   "Viewer@1234",   UserRole.viewer),
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

        # ── Financial records ─────────────────────────────────────────────────
        base_date = date(2024, 1, 1)
        for i in range(30):
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

    print("\n🎉 Seed complete! Login credentials:")
    print("   Admin   → admin@example.com    / Admin@123456")
    print("   Analyst → analyst@example.com  / Analyst@123")
    print("   Viewer  → viewer@example.com   / Viewer@1234")


if __name__ == "__main__":
    asyncio.run(seed())
