from fastapi import APIRouter, status

from talentscout.api.dependencies import AuthServiceDep, ClientIpDep, CurrentUserDep
from talentscout.api.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest, auth: AuthServiceDep, client_ip: ClientIpDep
) -> UserResponse:
    user = await auth.register(
        email=request.email,
        full_name=request.full_name,
        password=request.password,
        client_ip=client_ip,
    )
    return UserResponse(
        id=user.id, email=user.email, full_name=user.full_name, role=user.role.value
    )


@router.post("/login")
async def login(
    request: LoginRequest, auth: AuthServiceDep, client_ip: ClientIpDep
) -> TokenResponse:
    access, refresh = await auth.login(
        email=request.email, password=request.password, client_ip=client_ip
    )
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/refresh")
async def refresh(request: RefreshRequest, auth: AuthServiceDep) -> TokenResponse:
    access, new_refresh = await auth.refresh(request.refresh_token)
    return TokenResponse(access_token=access, refresh_token=new_refresh)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: RefreshRequest, auth: AuthServiceDep) -> None:
    await auth.logout(request.refresh_token)


@router.get("/me")
async def me(current_user: CurrentUserDep) -> UserResponse:
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role.value,
    )
