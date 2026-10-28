from dataclasses import dataclass
from datetime import datetime

from core.enums import DeliveryStatus


@dataclass(frozen=True)
class DeliveryResult:
    status: DeliveryStatus
    sent_at: datetime | None = None
    error: str | None = None
