from fastapi import APIRouter, HTTPException

from app.config import (
    load_cfg, save_cfg,
    llm_providers, save_llm_providers, save_llm_settings, llm_cfg
)
from app.schemas.llm import LLMProviderRequest, LLMSettingsRequest

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
    from app.config import retry_cfg
    return retry_cfg()


@router.get('/llm/providers')
def list_llm_providers():
    return llm_providers()


@router.post('/llm/providers')
def add_llm_provider(req: LLMProviderRequest):
    providers = llm_providers()
    if any(p.get('id') == req.id for p in providers):
        raise HTTPException(400, f'Provider {req.id} already exists')
    providers.append(req.model_dump())
    save_llm_providers(providers)
    return req.model_dump()


@router.put('/llm/providers/{provider_id}')
def update_llm_provider(provider_id: str, req: LLMProviderRequest):
    providers = llm_providers()
    for i, p in enumerate(providers):
        if p.get('id') == provider_id:
            providers[i] = req.model_dump()
            save_llm_providers(providers)
            return req.model_dump()
    raise HTTPException(404, f'Provider {provider_id} not found')


@router.delete('/llm/providers/{provider_id}')
def delete_llm_provider(provider_id: str):
    providers = llm_providers()
    before = len(providers)
    providers = [p for p in providers if p.get('id') != provider_id]
    save_llm_providers(providers)
    return {'deleted': before - len(providers)}


@router.post('/llm/providers/{provider_id}/test')
def test_llm_provider(provider_id: str):
    from app.services.review.llm import OpenAICompatibleClient

    providers = llm_providers()
    provider = next((p for p in providers if p.get('id') == provider_id), None)
    if not provider:
        raise HTTPException(404, f'Provider {provider_id} not found')

    client = OpenAICompatibleClient(provider)
    return client.test_connection()


@router.post('/llm/providers/{provider_id}/enable')
def enable_llm_provider(provider_id: str):
    providers = llm_providers()
    for p in providers:
        if p.get('id') == provider_id:
            p['enabled'] = True
            save_llm_providers(providers)
            return p
    raise HTTPException(404, f'Provider {provider_id} not found')


@router.post('/llm/providers/{provider_id}/disable')
def disable_llm_provider(provider_id: str):
    providers = llm_providers()
    for p in providers:
        if p.get('id') == provider_id:
            p['enabled'] = False
            save_llm_providers(providers)
            return p
    raise HTTPException(404, f'Provider {provider_id} not found')


@router.get('/llm/settings')
def get_llm_settings():
    lc = llm_cfg()
    return {
        'default': lc.get('default', ''),
        'fallback': lc.get('fallback', ''),
        'concurrent': lc.get('concurrent', 3),
        'retry_count': lc.get('retry_count', 2),
        'retry_delay': lc.get('retry_delay', 5)
    }


@router.put('/llm/settings')
def update_llm_settings(req: LLMSettingsRequest):
    save_llm_settings(req.model_dump())
    return req.model_dump()
