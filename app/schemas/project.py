from pydantic import BaseModel


class ProjectRequest(BaseModel):
    name: str
    svn_url: str
    enabled: bool = True
    owner_group: str = ''
    scan_window_days: int = 1
    teams_webhook_url: str = ''
