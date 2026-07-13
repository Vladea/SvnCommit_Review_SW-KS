import os
from pathlib import Path
from datetime import timezone, timedelta

import yaml
from dotenv import load_dotenv

load_dotenv()

APP_HOST = os.getenv('APP_HOST', '127.0.0.1')
APP_PORT = int(os.getenv('APP_PORT', '8000'))
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./data/svn_ai_review.db')
CONFIG_PATH = os.getenv('CONFIG_PATH', './config.yaml')
TIMEZONE_NAME = os.getenv('TIMEZONE', 'Asia/Shanghai')
LOCAL_OFFSET = int(os.getenv('LOCAL_TIMEZONE_OFFSET_HOURS', '8'))
LOCAL_TZ = timezone(timedelta(hours=LOCAL_OFFSET))
TEAMS_WEBHOOK_URL = os.getenv('TEAMS_WEBHOOK_URL', '')
SVN_USERNAME = os.getenv('SVN_USERNAME', '')
SVN_PASSWORD = os.getenv('SVN_PASSWORD', '')

Path('./data').mkdir(parents=True, exist_ok=True)
Path('./reports').mkdir(parents=True, exist_ok=True)

if DATABASE_URL.startswith('sqlite:///./'):
    db_path = DATABASE_URL.replace('sqlite:///./', '')
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)


def default_cfg():
    return {
        'timezone': 'Asia/Shanghai',
        'schedule': {'enabled': True, 'hour': 18, 'minute': 0},
        'scan': {
            'max_diff_chars_per_file': 12000,
            'include_extensions': [
                '.c', '.h', '.cpp', '.hpp', '.py',
                '.asl', '.inf', '.dsc', '.dec', '.vfr', '.uni',
                '.xml', '.json', '.yaml', '.yml'
            ],
            'exclude_paths': [
                'third_party/', 'vendor/', 'build/', 'output/', 'docs/'
            ],
            'retry': {
                'max_retries': 3,
                'delay': 5,
                'backoff': 2
            }
        },
        'llm': {
            'default': '',
            'fallback': '',
            'concurrent': 3,
            'retry_count': 2,
            'retry_delay': 5,
            'providers': []
        },
        'projects': []
    }


def load_cfg():
    p = Path(CONFIG_PATH)
    if not p.exists():
        p.write_text(yaml.safe_dump(default_cfg(), allow_unicode=True, sort_keys=False), encoding='utf-8')
    cfg = yaml.safe_load(p.read_text(encoding='utf-8')) or default_cfg()
    cfg.setdefault('schedule', {'entries': [{'hour': 18, 'minute': 0, 'enabled': True, 'notify_teams': True, 'notify_email': False}]})
    cfg.setdefault('scan', {})
    cfg.setdefault('llm', {
        'default': '', 'fallback': '', 'concurrent': 3,
        'retry_count': 2, 'retry_delay': 5, 'providers': []
    })
    cfg.setdefault('notifications', {
        'teams': {'enabled': True, 'webhook_url_ref': 'TEAMS_WEBHOOK_URL'},
        'email': {'enabled': False, 'smtp_host': '', 'smtp_port': 587, 'smtp_user': '',
                   'smtp_password_ref': 'EMAIL_SMTP_PASSWORD', 'from_addr': '', 'to_addrs': []}
    })
    cfg.setdefault('projects', [])
    _migrate_schedule(cfg)
    for prj in cfg.get('projects', []):
        prj.pop('branch', None)
        prj.setdefault('scan_window_days', 1)
        prj.setdefault('enabled', True)
        prj.setdefault('owner_group', '')
        prj.setdefault('teams_webhook_url', '')
    return cfg


def _migrate_schedule(cfg):
    sc = cfg.get('schedule', {})
    if 'entries' not in sc and 'hour' in sc:
        sc['entries'] = [{
            'hour': sc.get('hour', 18), 'minute': sc.get('minute', 0),
            'enabled': sc.get('enabled', True),
            'notify_teams': True, 'notify_email': False
        }]
        sc.pop('hour', None); sc.pop('minute', None); sc.pop('enabled', None)


def save_cfg(cfg):
    for prj in cfg.get('projects', []):
        prj.pop('branch', None)
    Path(CONFIG_PATH).write_text(
        yaml.safe_dump(cfg, allow_unicode=True, sort_keys=False), encoding='utf-8'
    )


def enabled_projects():
    return [p for p in load_cfg().get('projects', []) if p.get('enabled')]


def scan_cfg():
    sc = load_cfg().get('scan', {})
    sc.setdefault('max_diff_chars_per_file', 12000)
    sc.setdefault('include_extensions', [])
    sc.setdefault('exclude_paths', [])
    sc.setdefault('retry', {'max_retries': 3, 'delay': 5, 'backoff': 2})
    return sc


def schedule_cfg():
    sc = load_cfg().get('schedule', {})
    _migrate_schedule(load_cfg())
    return sc.get('entries', [{'hour': 18, 'minute': 0, 'enabled': True, 'notify_teams': True, 'notify_email': False}])


def notification_cfg():
    nc = load_cfg().get('notifications', {})
    nc.setdefault('teams', {'enabled': True, 'webhook_url_ref': 'TEAMS_WEBHOOK_URL'})
    nc.setdefault('email', {'enabled': False, 'smtp_host': '', 'smtp_port': 587, 'smtp_user': '',
                             'smtp_password_ref': 'EMAIL_SMTP_PASSWORD', 'from_addr': '', 'to_addrs': []})
    return nc


def rule_cfg():
    sc = load_cfg().get('scan', {})
    sc.setdefault('rules', {'merge_conflict': True, 'todo_marker': True, 'debug_print': True, 'memory_safety': True})
    return sc['rules']


def retry_cfg():
    return scan_cfg().get('retry', {'max_retries': 3, 'delay': 5, 'backoff': 2})


def auth_args(url=''):
    if url.startswith('file://'):
        return ['--non-interactive']
    args = ['--non-interactive', '--trust-server-cert-failures',
            'unknown-ca,cn-mismatch,expired,not-yet-valid,other']
    if SVN_USERNAME:
        args += ['--username', SVN_USERNAME]
    if SVN_PASSWORD:
        args += ['--password', SVN_PASSWORD]
    return args


def llm_cfg():
    lc = load_cfg().get('llm', {})
    lc.setdefault('default', '')
    lc.setdefault('fallback', '')
    lc.setdefault('concurrent', 3)
    lc.setdefault('retry_count', 2)
    lc.setdefault('retry_delay', 5)
    lc.setdefault('providers', [])
    return lc


def llm_providers():
    return llm_cfg().get('providers', [])


def get_active_llm_provider():
    cfg = llm_cfg()
    providers = cfg.get('providers', [])
    default_id = cfg.get('default', '')

    for p in providers:
        if p.get('enabled') and p.get('id') == default_id:
            api_key = os.getenv(p.get('api_key_ref', ''), '')
            if api_key or not p.get('api_key_ref'):
                return p

    for p in providers:
        if p.get('enabled') and p.get('id') != default_id:
            api_key = os.getenv(p.get('api_key_ref', ''), '')
            if api_key or not p.get('api_key_ref'):
                return p

    return None


def save_llm_providers(providers):
    cfg = load_cfg()
    cfg.setdefault('llm', {})
    cfg['llm']['providers'] = providers
    save_cfg(cfg)


def save_llm_settings(settings):
    cfg = load_cfg()
    cfg.setdefault('llm', {})
    for key in ('default', 'fallback', 'concurrent', 'retry_count', 'retry_delay'):
        if key in settings:
            cfg['llm'][key] = settings[key]
    save_cfg(cfg)
