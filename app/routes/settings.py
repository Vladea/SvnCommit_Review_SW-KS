from fastapi import APIRouter

from app.config import load_cfg, save_cfg, scan_cfg, retry_cfg

router = APIRouter(prefix='/settings', tags=['settings'])


@router.get('/scan')
def get_scan_settings():
    return load_cfg().get('scan', {})


@router.post('/scan')
def update_scan_settings(settings: dict):
    cfg = load_cfg()
    cfg['scan'] = settings
    save_cfg(cfg)
    return cfg['scan']


@router.get('/retry')
def get_retry_settings():
    return retry_cfg()
