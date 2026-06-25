from pydantic import BaseModel


class LLMProviderRequest(BaseModel):
    id: str
    name: str
    type: str = 'openai_compatible'
    api_base: str
    api_key_ref: str = ''
    model: str
    enabled: bool = True
    description: str = ''


class LLMSettingsRequest(BaseModel):
    default: str = ''
    fallback: str = ''
    concurrent: int = 3
    retry_count: int = 2
    retry_delay: int = 5
