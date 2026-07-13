from pydantic import BaseModel, Field
from typing import Optional


class ScanSettingsRequest(BaseModel):
    max_diff_chars_per_file: int = 12000
    max_files_per_commit: int = 10
    include_extensions: list[str] = []
    exclude_paths: list[str] = []
    retry: dict = Field(default_factory=lambda: {'max_retries': 3, 'delay': 5, 'backoff': 2})


class TeamsConfig(BaseModel):
    enabled: bool = True
    webhook_url_ref: str = 'TEAMS_WEBHOOK_URL'


class EmailConfig(BaseModel):
    enabled: bool = False
    smtp_host: str = ''
    smtp_port: int = 587
    smtp_user: str = ''
    smtp_password_ref: str = 'EMAIL_SMTP_PASSWORD'
    from_addr: str = ''
    to_addrs: list[str] = []


class NotificationSettingsRequest(BaseModel):
    teams: TeamsConfig = Field(default_factory=TeamsConfig)
    email: EmailConfig = Field(default_factory=EmailConfig)


class RulesSettingsRequest(BaseModel):
    merge_conflict: bool = True
    todo_marker: bool = True
    debug_print: bool = True
    memory_safety: bool = True
