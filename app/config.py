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
LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'mock')
LLM_API_BASE = os.getenv('LLM_API_BASE', '')
LLM_API_KEY = os.getenv('LLM_API_KEY', '')
LLM_MODEL = os.getenv('LLM_MODEL', '')
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
        'projects': []
    }


def load_cfg():
    p = Path(CONFIG_PATH)
    if not p.exists():
        p.write_text(yaml.safe_dump(default_cfg(), allow_unicode=True, sort_keys=False), encoding='utf-8')
    cfg = yaml.safe_load(p.read_text(encoding='utf-8')) or default_cfg()
    cfg.setdefault('schedule', {'enabled': True, 'hour': 18, 'minute': 0})
    cfg.setdefault('scan', {})
    cfg.setdefault('projects', [])
    for prj in cfg.get('projects', []):
        prj.pop('branch', None)
        prj.setdefault('scan_window_days', 1)
        prj.setdefault('enabled', True)
        prj.setdefault('owner_group', '')
        prj.setdefault('teams_webhook_url', '')
    return cfg


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
    return load_cfg().get('schedule', {'enabled': True, 'hour': 18, 'minute': 0})


def retry_cfg():
    return scan_cfg().get('retry', {'max_retries': 3, 'delay': 5, 'backoff': 2})


def auth_args():
    args = ['--non-interactive', '--trust-server-cert-failures',
            'unknown-ca,cn-mismatch,expired,not-yet-valid,other']
    if SVN_USERNAME:
        args += ['--username', SVN_USERNAME]
    if SVN_PASSWORD:
        args += ['--password', SVN_PASSWORD]
    return args
