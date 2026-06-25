from fastapi import APIRouter

from app.routes.dashboard import router as dashboard_router
from app.routes.projects import router as projects_router
from app.routes.scan import router as scan_router
from app.routes.schedule import router as schedule_router
from app.routes.reports import router as reports_router
from app.routes.issues import router as issues_router
from app.routes.authors import router as authors_router
from app.routes.settings import router as settings_router

api_router = APIRouter(prefix='/api')
api_router.include_router(dashboard_router)
api_router.include_router(projects_router)
api_router.include_router(scan_router)
api_router.include_router(schedule_router)
api_router.include_router(reports_router)
api_router.include_router(issues_router)
api_router.include_router(authors_router)
api_router.include_router(settings_router)
