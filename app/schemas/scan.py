from pydantic import BaseModel


class ScanRangeRequest(BaseModel):
    start_date: str
    end_date: str
    project_names: list[str] | None = None
    push_teams: bool = True
