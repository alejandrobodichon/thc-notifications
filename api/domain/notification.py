from dataclasses import dataclass


@dataclass(frozen=True)
class Notification:
    id: int
    title: str
    content: str
    channel: str
    channel_data: str
    created_at: str
    sent_at: str
    delivery_status: str
    user_id: str
