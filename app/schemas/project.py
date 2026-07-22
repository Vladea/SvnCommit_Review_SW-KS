from pydantic import BaseModel, Field, field_validator

VALID_URL_PREFIXES = ('svn://', 'svn+ssh://', 'http://', 'https://', 'file://')


class ProjectRequest(BaseModel):
    name: str = Field(..., min_length=1, description='项目名称')
    svn_url: str = Field(..., min_length=1, description='SVN 仓库地址')
    enabled: bool = True
    owner_group: str = ''
    scan_window_days: int = 1
    teams_webhook_url: str = ''

    @field_validator('svn_url')
    @classmethod
    def validate_url_scheme(cls, v: str):
        if not v.startswith(VALID_URL_PREFIXES):
            raise ValueError(f'SVN URL 必须以 {", ".join(VALID_URL_PREFIXES)} 开头')
        if '--' in v:
            raise ValueError('SVN URL 不能包含命令行标志')
        return v
