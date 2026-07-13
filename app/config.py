import os
import tempfile
import logging
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

logger = logging.getLogger('svn_ai_review')

DEFAULTS = {
    'timezone': 'Asia/Shanghai',
    'schedule': {'entries': [
        {'hour': 18, 'minute': 0, 'enabled': True, 'notify_teams': True, 'notify_email': False}
    ]},
    'scan': {
        'max_diff_chars_per_file': 12000,
        'max_files_per_commit': 10,
        'include_extensions': [
            '.c', '.h', '.cpp', '.hpp', '.py',
            '.asl', '.inf', '.dsc', '.dec', '.vfr', '.uni',
            '.xml', '.json', '.yaml', '.yml'
        ],
        'exclude_paths': [
            'third_party/', 'vendor/', 'build/', 'output/', 'docs/'
        ],
        'rules': {'merge_conflict': True, 'todo_marker': True, 'debug_print': True, 'memory_safety': True},
        'retry': {'max_retries': 3, 'delay': 5, 'backoff': 2},
    },
    'llm': {
        'default': '', 'fallback': '', 'concurrent': 3,
        'retry_count': 2, 'retry_delay': 5, 'providers': [],
    },
    'notifications': {
        'teams': {'enabled': True, 'webhook_url_ref': 'TEAMS_WEBHOOK_URL'},
        'email': {'enabled': False, 'smtp_host': '', 'smtp_port': 587, 'smtp_user': '',
                   'smtp_password_ref': 'EMAIL_SMTP_PASSWORD', 'from_addr': '', 'to_addrs': []},
    },
    'projects': [],
}

_cache = None
_cache_mtime = 0.0


def _deep_merge(default: dict, override: dict) -> dict:
    for k, v in default.items():
        if k not in override:
            override[k] = v
        elif isinstance(v, dict) and isinstance(override[k], dict):
            _deep_merge(v, override[k])
    return override


def _normalize(cfg: dict) -> dict:
    if cfg.get('schedule', {}).get('enabled') is not None and 'entries' not in cfg.get('schedule', {}):
        sc = cfg['schedule']
        sc['entries'] = [{
            'hour': sc.pop('hour', 18), 'minute': sc.pop('minute', 0),
            'enabled': sc.pop('enabled', True),
            'notify_teams': True, 'notify_email': False,
        }]

    for prj in cfg.get('projects', []):
        prj.pop('branch', None)
        prj.setdefault('scan_window_days', 1)
        prj.setdefault('enabled', True)
        prj.setdefault('owner_group', '')
        prj.setdefault('teams_webhook_url', '')
    return cfg


def _invalidate_cache():
    global _cache, _cache_mtime
    _cache = None
    _cache_mtime = 0.0


def load_cfg() -> dict:
    global _cache, _cache_mtime
    p = Path(CONFIG_PATH)
    mtime = p.stat().st_mtime if p.exists() else 0.0

    if _cache is not None and mtime <= _cache_mtime:
        return _cache

    if not p.exists():
        example = Path('config.example.yaml')
        if example.exists():
            import shutil
            shutil.copy2(example, p)
        else:
            p.write_text(yaml.safe_dump(DEFAULTS, allow_unicode=True, sort_keys=False), encoding='utf-8')

    try:
        raw = yaml.safe_load(p.read_text(encoding='utf-8'))
    except yaml.YAMLError as e:
        logger.error(f'Config parse error: {e}. Using defaults.')
        raw = None

    cfg = _deep_merge(dict(DEFAULTS), raw) if raw else dict(DEFAULTS)
    _normalize(cfg)
    _cache = cfg
    _cache_mtime = mtime
    return cfg


def save_cfg(cfg: dict):
    global _cache, _cache_mtime
    for prj in cfg.get('projects', []):
        prj.pop('branch', None)
    yaml_text = yaml.safe_dump(cfg, allow_unicode=True, sort_keys=False)
    p = Path(CONFIG_PATH)
    fd, tmp = tempfile.mkstemp(dir=p.parent, prefix='.config_', suffix='.tmp')
    try:
        os.write(fd, yaml_text.encode('utf-8'))
        os.fsync(fd)
    finally:
        os.close(fd)
    os.replace(tmp, str(p))
    _cache = cfg
    _cache_mtime = p.stat().st_mtime


def enabled_projects() -> list[dict]:
    return [p for p in load_cfg().get('projects', []) if p.get('enabled')]


def scan_cfg() -> dict:
    return load_cfg().get('scan', {})


def schedule_cfg() -> list[dict]:
    sc = load_cfg().get('schedule', {})
    return sc.get('entries', [{'hour': 18, 'minute': 0, 'enabled': True, 'notify_teams': True, 'notify_email': False}])


def notification_cfg() -> dict:
    return load_cfg().get('notifications', {})


def rule_cfg() -> dict:
    return scan_cfg().get('rules', {})


def retry_cfg() -> dict:
    return scan_cfg().get('retry', {'max_retries': 3, 'delay': 5, 'backoff': 2})


def auth_args(url: str = '') -> list[str]:
    if url.startswith('file://'):
        return ['--non-interactive']
    args = ['--non-interactive', '--trust-server-cert-failures',
            'unknown-ca,cn-mismatch,expired,not-yet-valid,other']
    if SVN_USERNAME:
        args += ['--username', SVN_USERNAME]
    if SVN_PASSWORD:
        args += ['--password', SVN_PASSWORD]
    return args


def llm_cfg() -> dict:
    return load_cfg().get('llm', {})


def llm_providers() -> list[dict]:
    return llm_cfg().get('providers', [])


def get_active_llm_provider() -> dict | None:
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


def save_llm_providers(providers: list[dict]):
    cfg = load_cfg()
    cfg.setdefault('llm', {})
    cfg['llm']['providers'] = providers
    save_cfg(cfg)


def save_llm_settings(settings: dict):
    cfg = load_cfg()
    cfg.setdefault('llm', {})
    for key in ('default', 'fallback', 'concurrent', 'retry_count', 'retry_delay'):
        if key in settings:
            cfg['llm'][key] = settings[key]
    save_cfg(cfg)
