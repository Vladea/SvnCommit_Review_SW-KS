import logging

import requests

from app.config import TEAMS_WEBHOOK_URL

logger = logging.getLogger('svn_ai_review')


def send_teams(text, url=''):
    url = url or TEAMS_WEBHOOK_URL
    if not url:
        return False, 'TEAMS_WEBHOOK_URL is empty'

    try:
        r = requests.post(url, json={'text': text}, timeout=30)
        ok = 200 <= r.status_code < 300
        msg = 'OK' if ok else f'HTTP {r.status_code}: {r.text[:200]}'
        if ok:
            logger.info('Teams notification sent successfully')
        else:
            logger.warning(f'Teams notification failed: {msg}')
        return ok, msg
    except Exception as e:
        logger.error(f'Teams notification error: {e}')
        return False, str(e)
