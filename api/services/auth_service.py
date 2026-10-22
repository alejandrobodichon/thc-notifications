from core.auth import create_access_token, verify_password
from core.exceptions import InvalidCredentials
from repositories.user_repository import UserRepository


class AuthService:
    def __init__(self, user_repository: UserRepository):
        self._user_repository = user_repository

    async def login(self, username: str, password: str) -> str:
        user = await self._user_repository.get_by_username(username.lower())
        if user is None or not verify_password(password, user.password_hash):
            raise InvalidCredentials()
        return create_access_token(user.id)
