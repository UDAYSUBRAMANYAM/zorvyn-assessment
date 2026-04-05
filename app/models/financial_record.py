"""Financial record ORM model."""
import enum
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Enum, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class RecordType(str, enum.Enum):
    income = "income"
    expense = "expense"


class FinancialRecord(Base):
    __tablename__ = "financial_records"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    type: Mapped[RecordType] = mapped_column(Enum(RecordType), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    record_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Soft delete support
    is_deleted: Mapped[bool] = mapped_column(default=False, index=True)

    # Audit
    created_by: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False
    )
    updated_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<FinancialRecord id={self.id} type={self.type} "
            f"amount={self.amount} category={self.category}>"
        )
