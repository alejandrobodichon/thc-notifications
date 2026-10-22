from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from dependencies import AuthServiceDep
from schemas.auth import Token

router = APIRouter()


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], service: AuthServiceDep
):
    token = await service.login(form_data.username.lower(), form_data.password)
    return Token(access_token=token, token_type="bearer")
