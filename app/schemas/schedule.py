from pydantic import BaseModel


class ScheduleRequest(BaseModel):
    enabled: bool = True
    hour: int = 18
    minute: int = 0
