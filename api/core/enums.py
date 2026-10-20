from enum import StrEnum


class DeliveryStatus(StrEnum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class Channel(StrEnum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"