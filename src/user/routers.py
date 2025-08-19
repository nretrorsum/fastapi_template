from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.routers import auth_dependency
from src.database.connection import get_db
from src.user import schemas as user_schemas
from src.user.models import User
from src.user.services import UserService

user_router = APIRouter(prefix="/user", tags=["user"])


@user_router.post("/create", response_model=user_schemas.UserResponse)
async def create_user(
        user: user_schemas.UserCreate,
        session: AsyncSession = Depends(get_db)
):
    try:
        return await UserService.create_user_service(user, session)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@user_router.get("/get/all")
async def get_all_users(
        auth_user: auth_dependency,
        session: AsyncSession = Depends(get_db),
) -> list[user_schemas.UserResponse]:

    return await UserService.get_all_users(session)


@user_router.get("/get/email/{email}", response_model=user_schemas.UserResponse)
async def get_user_by_email(
        email: str,
        auth_user: auth_dependency,
        session: AsyncSession = Depends(get_db),
):
    print(f"User email: {email}")
    user = await UserService.get_user_by_email(email, session)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@user_router.get("/get/id/{user_id}", response_model=user_schemas.UserResponse)
async def get_user_by_id(
        user_id: UUID,
        auth_user: auth_dependency,
        session: AsyncSession = Depends(get_db)
):
    user = await User.get_by_field(session, 'id', user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@user_router.patch("/update/{user_id}", response_model=user_schemas.UserResponse)
async def update_user(
        user_id: UUID,
        auth_user: auth_dependency,
        user: user_schemas.UserUpdate,
        session: AsyncSession = Depends(get_db)
):
    data = user.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No data provided for update"
        )

    updated_user = await UserService.update_user(data, user_id, session)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return updated_user


@user_router.delete("/delete/{user_id}")
async def delete_user(
        user_id: UUID,
        auth_user: auth_dependency,
        session: AsyncSession = Depends(get_db)
):
    deleted_count = await UserService.delete_user(user_id, session)
    if deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return {"message": "User deleted successfully"}


@user_router.post("/create-batch", response_model=list[user_schemas.UserResponse])
async def create_users_batch(
        users: list[user_schemas.UserCreate],
        session: AsyncSession = Depends(get_db)
):
    if len(users) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Too many users in batch (max 100)"
        )

    return await UserService.create_users_batch(users, session)

@user_router.post('/user_info/create/{user_id}')
async def create_user_info(
        user_id: UUID,
        user_info: user_schemas.CreateUserInfo,
        session: AsyncSession = Depends(get_db)
):
    data = user_info.model_dump(exclude_unset=True)
    print(f"User info: {data}")
    try:
        return await UserService.save_user_data(user_id, data, session)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


#TODO
# @user_router.post('avatar/create/{user_id}')
# async def create_avatar(
#         avatar: UploadFile = File(...),
# ):
#     extension = avatar.filename.split(".")[-1].lower()
#     if extension not in ["jpg", "jpeg", "png"]:
#         raise HTTPException(status_code=400, detail="Invalid file type")
#     ended_path = os.path.join('/app',UPLOAD_DIR, avatar.filename)
#     contents = await avatar.read()
#     async with aiofiles.open(ended_path, "wb") as f:
#         await f.write(contents)
#     return {"filename": avatar.filename, "path": ended_path}
