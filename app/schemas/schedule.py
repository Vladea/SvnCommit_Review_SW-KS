from pydantic import BaseModel


class ScheduleEntryRequest(BaseModel):
    hour: int = 18
    minute: int = 0
    enabled: bool = True
    notify_teams: bool = True
    notify_email: bool = False


class ScheduleRequest(BaseModel):
    entries: list[ScheduleEntryRequest]
