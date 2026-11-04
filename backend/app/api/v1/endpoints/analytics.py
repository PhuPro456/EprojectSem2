from fastapi import APIRouter, Depends

from app.api.deps import DatabaseSession, get_current_admin
from app.crud.analytics import build_overview
from app.schemas.analytics import AnalyticsOverview

router = APIRouter(
    prefix="/analytics",
    tags=["analytics"],
    dependencies=[Depends(get_current_admin)],
)


@router.get("/overview", response_model=AnalyticsOverview)
def overview(db: DatabaseSession) -> AnalyticsOverview:
    return build_overview(db)
