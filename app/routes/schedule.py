from fastapi import APIRouter, HTTPException

from app.config import load_cfg, save_cfg
from app.schemas.schedule import ScheduleRequest
from app.scheduler import reload_schedule

router = APIRouter(tags=['schedule'])


@router.get('/schedule')
def get_schedule():
    from app.config import schedule_cfg
    return schedule_cfg()


@router.post('/schedule')
def set_schedule(req: ScheduleRequest):
    if not (0 <= req.hour <= 23 and 0 <= req.minute <= 59):
        raise HTTPException(400, 'hour/minute invalid')
    cfg = load_cfg()
    cfg['schedule'] = req.model_dump()
    save_cfg(cfg)
    reload_schedule()
    return cfg['schedule']
