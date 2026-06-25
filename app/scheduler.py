import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.config import TIMEZONE_NAME, schedule_cfg
from app.services.scanner import run_daily_job

logger = logging.getLogger('svn_ai_review')

scheduler = BackgroundScheduler(timezone=TIMEZONE_NAME)


def reload_schedule():
    for job in scheduler.get_jobs():
        if job.id.startswith('daily_svn_review'):
            scheduler.remove_job(job.id)

    entries = schedule_cfg()
    for i, entry in enumerate(entries):
        if entry.get('enabled', True):
            job_id = f'daily_svn_review_{i}'
            scheduler.add_job(
                run_daily_job, 'cron',
                hour=int(entry.get('hour', 18)),
                minute=int(entry.get('minute', 0)),
                id=job_id,
                replace_existing=True
            )
            logger.info(f'Schedule [{job_id}] added: daily at {entry.get("hour", 18):02d}:{entry.get("minute", 0):02d}')
    if not any(e.get('enabled', True) for e in entries):
        logger.info('All schedule entries disabled')
