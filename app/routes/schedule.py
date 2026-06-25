from fastapi import APIRouter, HTTPException

from app.config import load_cfg, save_cfg, schedule_cfg
from app.schemas.schedule import ScheduleRequest
from app.scheduler import reload_schedule

router = APIRouter(tags=['schedule'])


@router.get('/schedule')
def get_schedule():
    return schedule_cfg()


@router.post('/schedule')
def set_schedule(req: ScheduleRequest):
    for entry in req.entries:
        if not (0 <= entry.hour <= 23 and 0 <= entry.minute <= 59):
            raise HTTPException(400, 'hour/minute invalid')
    cfg = load_cfg()
    cfg['schedule'] = {'entries': [e.model_dump() for e in req.entries]}
    save_cfg(cfg)
    reload_schedule()
    return cfg['schedule']
