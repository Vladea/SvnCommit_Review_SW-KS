from pydantic import BaseModel, Field


class ProjectRequest(BaseModel):
    name: str = Field(..., min_length=1, description='项目名称')
    svn_url: str = Field(..., min_length=1, description='SVN 仓库地址')
    enabled: bool = True
    owner_group: str = ''
    scan_window_days: int = 1
    teams_webhook_url: str = ''
