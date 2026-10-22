
from fastapi import APIRouter, status

from dependencies import CurrentUser, UserServiceDep
from schemas.user import UserCreate, UserPrivate, UserProfileResponse, UserUpdate

router = APIRouter()


@router.get("/me", response_model=UserPrivate)
async def get_current_user(current_user: CurrentUser):
    return current_user

@router.get("", response_model = list[UserProfileResponse])
async def get_users(service: UserServiceDep):
    return await service.list_users()

@router.post("", response_model= UserPrivate, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, service: UserServiceDep):
    return await service.create(user)

@router.get("/{user_id}", response_model= UserProfileResponse)
async def get_user(user_id: int, service: UserServiceDep):
    return await service.get_profile(user_id)

@router.patch("/{user_id}", response_model= UserPrivate)
async def update_user(
    user_id: int, data: UserUpdate, current_user: CurrentUser, service: UserServiceDep
):
    return await service.update(user_id, data, current_user.id)

@router.delete("/{user_id}", status_code= status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, current_user: CurrentUser, service: UserServiceDep):
    return await service.delete(user_id, current_user.id)



