from core.auth import hash_password
from core.exceptions import (
    EmailAlreadyExists,
    NotAuthorized,
    UsernameAlreadyExists,
    UserNotFound,
)
from domain.user_profile import UserProfile
from models.user import User
from repositories.user_repository import UserRepository
from schemas.user import UserCreate, UserUpdate


class UserService:
    def __init__(self, user_repo: UserRepository):
        self._repo = user_repo

    async def create(self, user_create: UserCreate) -> User:
        if await self._repo.exist_by_email(user_create.email):
            raise EmailAlreadyExists()

        if await self._repo.exist_by_username(user_create.username):
            raise UsernameAlreadyExists()

        user = User(
            username=user_create.username,
            email=user_create.email,
            password_hash=hash_password(user_create.password),
        )

        return await self._repo.save(user=user)

    async def get(self, user_id: int) -> User:
        user = await self._repo.get_by_id(user_id)

        if user is None:
            raise UserNotFound()

        return user

    async def get_profile(self, user_id: int) -> UserProfile:
        user = await self._repo.get_by_id(user_id)

        if user is None:
            raise UserNotFound()

        return UserProfile(id=user.id, email=user.email, username=user.username)

    async def list_users(self) -> list[UserProfile]:
        users = await self._repo.get_all()

        return [UserProfile(id=user.id, email=user.email, username=user.username) for user in users]

    async def update(self, user_id: int, data: UserUpdate, current_user_id: int) -> User:
        if user_id != current_user_id:
            raise NotAuthorized()

        user = await self.get(user_id)

        if data.email is not None and data.email != user.email:
            if await self._repo.exist_by_email(data.email):
                raise EmailAlreadyExists()
        if data.username is not None and data.username != user.username:
            if await self._repo.exist_by_username(data.username):
                raise UsernameAlreadyExists()

        for field, value in data.model_dump(exclude_unset=True, exclude_none=True).items():
            setattr(user, field, value)

        return await self._repo.save(user)

    async def delete(self, user_id: int, current_user_id: int) -> None:
        if user_id != current_user_id:
            raise NotAuthorized()
        user = await self.get(user_id)

        await self._repo.delete(user)
