import threading
import uuid
import time
from datetime import datetime, timedelta

_store = {}
_lock = threading.Lock()
_EXPIRE = timedelta(hours=2)
_CLEANUP_INTERVAL = 600


def _periodic_cleanup():
    while True:
        time.sleep(_CLEANUP_INTERVAL)
        _cleanup()


_cleaner = threading.Thread(target=_periodic_cleanup, daemon=True)
_cleaner.start()


def create_id():
    return uuid.uuid4().hex[:12]


def create(total_commits, matched_logs, skipped_logs, is_preview=False):
    sid = create_id()
    with _lock:
        _store[sid] = {
            'status': 'running',
            'total_commits': total_commits,
            'completed': 0,
            'current_project': '',
            'current_revision': '',
            'current_file': '',
            'is_preview': is_preview,
            'matched_logs': matched_logs,
            'skipped_logs': skipped_logs,
            'result': None,
            'error': None,
            'created_at': datetime.utcnow(),
        }
    return sid


def update(sid, **kwargs):
    with _lock:
        if sid in _store:
            _store[sid].update(kwargs)


def get(sid):
    _cleanup()
    with _lock:
        return dict(_store.get(sid, {}))


def finish(sid, result):
    with _lock:
        if sid in _store:
            _store[sid]['status'] = 'done'
            _store[sid]['result'] = result


def fail(sid, error):
    with _lock:
        if sid in _store:
            _store[sid]['status'] = 'error'
            _store[sid]['error'] = str(error)


def cancel(sid):
    with _lock:
        if sid in _store:
            _store[sid]['status'] = 'cancelled'
            _store[sid]['cancelled'] = True


def is_cancelled(sid):
    with _lock:
        entry = _store.get(sid, {})
        return entry.get('cancelled', False)


def _cleanup():
    cutoff = datetime.utcnow() - _EXPIRE
    with _lock:
        expired = [k for k, v in _store.items() if v.get('created_at', datetime.utcnow()) < cutoff]
        for k in expired:
            del _store[k]
