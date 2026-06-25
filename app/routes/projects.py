from fastapi import APIRouter, HTTPException

from app.config import load_cfg, save_cfg
from app.schemas.project import ProjectRequest

router = APIRouter(prefix='/projects', tags=['projects'])


@router.get('')
def list_projects():
    return load_cfg().get('projects', [])


@router.post('')
def add_project(req: ProjectRequest):
    cfg = load_cfg()
    arr = cfg.setdefault('projects', [])
    if any(p.get('name') == req.name for p in arr):
        raise HTTPException(400, 'Project exists')
    arr.append(req.model_dump())
    save_cfg(cfg)
    return req.model_dump()


@router.delete('/{name}')
def delete_project(name: str):
    cfg = load_cfg()
    before = len(cfg.get('projects', []))
    cfg['projects'] = [p for p in cfg.get('projects', []) if p.get('name') != name]
    save_cfg(cfg)
    return {'deleted': before - len(cfg['projects'])}


def _set_enabled(name, en):
    cfg = load_cfg()
    for p in cfg.get('projects', []):
        if p.get('name') == name:
            p['enabled'] = en
            save_cfg(cfg)
            return p
    raise HTTPException(404, 'Project not found')


@router.post('/{name}/enable')
def enable_project(name: str):
    return _set_enabled(name, True)


@router.post('/{name}/disable')
def disable_project(name: str):
    return _set_enabled(name, False)
