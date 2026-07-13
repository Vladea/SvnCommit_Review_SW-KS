import logging
import re
import subprocess
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

from app.config import auth_args, scan_cfg, retry_cfg, LOCAL_TZ

logger = logging.getLogger('svn_ai_review')


def run_cmd(args, timeout=120):
    p = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       text=True, encoding='utf-8', errors='ignore', timeout=timeout)
    if p.returncode != 0:
        raise RuntimeError(p.stderr.strip())
    return p.stdout


def run_cmd_with_retry(args):
    if any(str(a).startswith('file://') for a in args):
        return run_cmd(args)

    rcfg = retry_cfg()
    max_retries = rcfg.get('max_retries', 3)
    delay = rcfg.get('delay', 5)
    backoff = rcfg.get('backoff', 2)

    last_err = None
    for attempt in range(max_retries + 1):
        try:
            return run_cmd(args)
        except Exception as e:
            last_err = e
            if attempt < max_retries:
                wait = delay * (backoff ** attempt)
                logger.warning(f'SVN command failed (attempt {attempt + 1}/{max_retries + 1}): {e}. Retrying in {wait}s...')
                time.sleep(wait)
    raise last_err


def normalize_date_text(d):
    return datetime.strptime(d, '%Y-%m-%d').date()


def end_date_plus_one(end_date):
    return (normalize_date_text(end_date) + timedelta(days=1)).isoformat()


def parse_svn_time_to_local(text):
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace('Z', '+00:00')).astimezone(LOCAL_TZ)
    except Exception:
        return None


def svn_logs(url, start_date, end_date):
    svn_end = end_date_plus_one(end_date)
    root = ET.fromstring(
        run_cmd_with_retry(['svn', 'log', url, '-r', f'{{{start_date}}}:{{{svn_end}}}', '--xml'] + auth_args(url))
    )
    logs = []
    for e in root.findall('logentry'):
        logs.append({
            'revision': e.attrib.get('revision', ''),
            'author': (e.findtext('author') or '').strip(),
            'commit_time': (e.findtext('date') or '').strip(),
            'message': (e.findtext('msg') or '').strip()
        })
    return logs


def filter_logs_by_real_commit_date(logs, start_date, end_date):
    sd = normalize_date_text(start_date)
    ed = normalize_date_text(end_date)
    out = []
    skipped = []
    for log in logs:
        ct = parse_svn_time_to_local(log.get('commit_time', ''))
        local_date = ct.date() if ct else None
        log['commit_date_local'] = local_date.isoformat() if local_date else 'unknown'
        log['commit_time_local'] = ct.strftime('%Y-%m-%d %H:%M:%S') if ct else 'unknown'
        if local_date is not None and sd <= local_date <= ed:
            out.append(log)
        else:
            skipped.append({
                'revision': log.get('revision', ''),
                'author': log.get('author', ''),
                'commit_time': log.get('commit_time', ''),
                'commit_date_local': log.get('commit_date_local', 'unknown'),
                'commit_time_local': log.get('commit_time_local', 'unknown')
            })
    return out, skipped


def svn_diff_safe(url, rev):
    last = ''
    urls = [url] if url.startswith('file://') else [url, f'{url}@{rev}', f'{url}@HEAD']
    for u in urls:
        try:
            return run_cmd_with_retry(['svn', 'diff', u, '-c', rev] + auth_args(url))
        except Exception as e:
            last = str(e)
    raise RuntimeError(last)


def split_diff(diff_text):
    out = {}
    for part in re.split(r'(?=^Index: .*$)', diff_text, flags=re.M):
        m = re.search(r'^Index: (.+)$', part, re.M)
        if m:
            out[m.group(1).strip()] = part
    return out


def should_review(path):
    cfg = scan_cfg()
    lower = str(path).lower().replace('\\', '/')
    exclude = [str(x).lower() for x in cfg.get('exclude_paths', [])]
    include = [str(x).lower() for x in cfg.get('include_extensions', [])]
    if any(x in lower for x in exclude):
        return False
    return any(lower.endswith(x) for x in include) if include else True


def svn_info(url):
    result = run_cmd_with_retry(['svn', 'info', url] + auth_args(url))
    return result
