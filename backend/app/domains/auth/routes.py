from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db
from backend.app.domains.auth.schemas import UserCreate, UserRead, LoginRequest, Token
from backend.app.domains.auth.services import AuthService
from backend.app.domains.auth.models import User

router = APIRouter(prefix="/auth", tags=["authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    FastAPI dependency resolver that fetches the currently authenticated user session.
    """
    auth_service = AuthService(db)
    return await auth_service.get_current_user_from_token(token)

@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(schema: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Register a new user account on the CPQ platform.
    """
    auth_service = AuthService(db)
    return await auth_service.register_user(schema)

@router.post("/login", response_model=Token)
async def login(credentials: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Log in with email credentials and retrieve a JWT Access Token.
    """
    auth_service = AuthService(db)
    return await auth_service.authenticate(credentials)

@router.get("/me", response_model=UserRead)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Get profile information of the currently authenticated user.
    """
    return current_user
