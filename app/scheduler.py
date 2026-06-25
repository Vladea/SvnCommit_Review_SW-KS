import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.config import TIMEZONE_NAME, schedule_cfg
from app.services.scanner import run_daily_job

logger = logging.getLogger('svn_ai_review')

scheduler = BackgroundScheduler(timezone=TIMEZONE_NAME)


def reload_schedule():
    cfg = schedule_cfg()
    try:
        scheduler.remove_job('daily_svn_review')
    except Exception:
        pass
    if cfg.get('enabled', True):
        scheduler.add_job(
            run_daily_job, 'cron',
            hour=int(cfg.get('hour', 18)),
            minute=int(cfg.get('minute', 0)),
            id='daily_svn_review',
            replace_existing=True
        )
        logger.info(f'Schedule reloaded: daily at {cfg.get("hour", 18):02d}:{cfg.get("minute", 0):02d}')
    else:
        logger.info('Schedule disabled')
