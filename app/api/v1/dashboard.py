"""Dashboard aggregation router.

Permissions
-----------
- analyst + admin can access full dashboard summary
- viewer is intentionally excluded (read-only basic records only)
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import require_roles
from app.models.user import User, UserRole
from app.schemas.dashboard import DashboardSummary
from app.services.dashboard_service import get_dashboard_summary

router = APIRouter()

_ANALYTICS_ROLES = (UserRole.analyst, UserRole.admin)


@router.get("/summary", response_model=DashboardSummary)
async def dashboard_summary(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(*_ANALYTICS_ROLES)),
):
    """
    Return aggregated dashboard data:
    - Total income / expense / net balance
    - Category-wise totals
    - Monthly income vs expense trends
    - 10 most recent records

    **Accessible by:** analyst, admin
    """
    return await get_dashboard_summary(db)
