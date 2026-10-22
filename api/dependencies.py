import secrets
from typing import Annotated

from fastapi import Depends, Header, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from clients.sms_queue_publisher import SmsQueuePublisher
from core.auth import verify_access_token
from core.config import settings
from core.database import get_db
from core.enums import Channel
from core.exceptions import NotAuthenticated
from core.strategy.email_notification_strategy import EmailNotificationStrategy
from core.strategy.notification_strategy import NotificationStrategy
from core.strategy.push_notification_strategy import PushNotificationStrategy
from core.strategy.sms_notification_strategy import SmsNotificationStrategy
from models.user import User
from repositories.notification_repository import NotificationRepository
from repositories.user_repository import UserRepository
from services.auth_service import AuthService
from services.notification_service import NotificationService
from services.user_service import UserService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

def get_user_repository(db: Annotated[AsyncSession, Depends(get_db)]) -> UserRepository:
    return UserRepository(db)


def get_user_service(
    repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> UserService:
    return UserService(repo)

UserServiceDep = Annotated[UserService, Depends(get_user_service)]


def get_notification_repository(
        db: Annotated[AsyncSession, Depends(get_db)]
) -> NotificationRepository:
    return NotificationRepository(db)


def get_auth_service(
    repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> AuthService:
    return AuthService(repo)

AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> User:
    user_id = verify_access_token(token)
    if user_id is None:
        raise NotAuthenticated()
    user = await repo.get_by_id(user_id)
    if user is None:
        raise NotAuthenticated()
    return user

CurrentUser = Annotated[User, Depends(get_current_user)]

def get_sms_publisher(request: Request) -> SmsQueuePublisher:
    return request.app.state.sms_publisher

SmsPublisherDep = Annotated[SmsQueuePublisher, Depends(get_sms_publisher)]


def get_channel_registry(sms_publisher: SmsPublisherDep) -> dict[Channel, NotificationStrategy]:
    return {
        Channel.EMAIL: EmailNotificationStrategy(),
        Channel.PUSH: PushNotificationStrategy(),
        Channel.SMS: SmsNotificationStrategy(sms_publisher),
    }

ChannelRegistryDep = Annotated[
    dict[Channel, NotificationStrategy], Depends(get_channel_registry)
]

def get_notification_service(
    repo: Annotated[NotificationRepository, Depends(get_notification_repository)],
    registry: ChannelRegistryDep,
) -> NotificationService:
    return NotificationService(repo, registry)

NotificationServiceDep = Annotated[NotificationService, Depends(get_notification_service)]

def verify_internal_api_key(x_api_key: Annotated[str, Header()]) -> None:
    if not secrets.compare_digest(x_api_key, settings.internal_api_key):
        raise NotAuthenticated()

InternalApiKeyDep = Annotated[None, Depends(verify_internal_api_key)]