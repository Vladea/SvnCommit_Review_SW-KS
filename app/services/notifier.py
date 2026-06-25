import json
import logging
import os
import smtplib
from email.mime.text import MIMEText

import requests

from app.config import notification_cfg, TEAMS_WEBHOOK_URL

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


def send_email(text, cfg=None):
    cfg = cfg or notification_cfg().get('email', {})
    if not cfg.get('enabled') or not cfg.get('smtp_host'):
        return False, 'Email not configured'

    host = cfg['smtp_host']
    port = cfg['smtp_port']
    user = cfg.get('smtp_user', '') or cfg.get('from_addr', '')
    password = os.getenv(cfg.get('smtp_password_ref', ''), '')
    from_addr = cfg.get('from_addr', '')
    to_addrs = cfg.get('to_addrs', [])

    if not password or not from_addr or not to_addrs:
        return False, 'Email config incomplete'

    subject = text.split('\n')[0].strip() if text else 'SVN AI Review Report'
    body = text if text else ''

    msg = MIMEText(body, 'plain', 'utf-8')
    msg['Subject'] = subject
    msg['From'] = from_addr
    msg['To'] = ', '.join(to_addrs)

    try:
        server = smtplib.SMTP(host, port, timeout=30)
        server.starttls()
        server.login(user, password)
        server.sendmail(from_addr, to_addrs, msg.as_string())
        server.quit()
        logger.info(f'Email sent to {len(to_addrs)} recipients')
        return True, 'OK'
    except Exception as e:
        logger.error(f'Email notification error: {e}')
        return False, str(e)


def send_notification(report_text, channels=None):
    channels = channels or notification_cfg()
    results = {}

    teams_cfg = channels.get('teams', {})
    if teams_cfg.get('enabled'):
        ok, msg = send_teams(report_text)
        results['teams'] = {'ok': ok, 'msg': msg}

    email_cfg = channels.get('email', {})
    if email_cfg.get('enabled'):
        ok, msg = send_email(report_text, email_cfg)
        results['email'] = {'ok': ok, 'msg': msg}

    return results


def test_teams_connection():
    nc = notification_cfg()
    teams_cfg = nc.get('teams', {})
    if not teams_cfg.get('enabled'):
        return False, 'Teams is disabled in config'

    url = os.getenv(teams_cfg.get('webhook_url_ref', ''), '') or TEAMS_WEBHOOK_URL
    if not url:
        return False, 'Teams webhook URL not configured'

    return send_teams('Test notification from SVN AI Review V2.0', url)


def test_email_connection():
    email_cfg = notification_cfg().get('email', {})
    if not email_cfg.get('enabled'):
        return False, 'Email is disabled in config'
    return send_email('Test notification from SVN AI Review V2.0', email_cfg)
