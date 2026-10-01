from typing import Optional, TypedDict


class BotState(TypedDict, total=False):
    messages: list
    user_input: str
    activity: str
    location: str
    time_period: str
    target_hour: Optional[int]
    target_group: str
    latitude: float
    longitude: float
    weather: dict
    matched_sops: list
    selected_sop: Optional[dict]
    error: str
    response: str