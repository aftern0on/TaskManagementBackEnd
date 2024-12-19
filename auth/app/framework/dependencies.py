from fastapi import Depends, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.entities.user import UserEntity
from app.framework.database import AsyncSession
from app.framework.factory import TokenFactory
from app.framework.redis import redis_client
from app.framework.repository import UserRepository, TokenRepository
from app.config import SECRET_KEY, ENCODE_ALGORITHM
from app.use_cases.auth_service import auth_case


async def get_db() -> AsyncSession:
    async with AsyncSession() as session:
        yield session


async def get_user_repo(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


async def get_token_repo(user_repo: UserRepository = Depends(get_user_repo)) -> TokenRepository:
    return TokenRepository(redis_client, user_repo)


async def get_token_factory() -> TokenFactory:
    return TokenFactory(SECRET_KEY, ENCODE_ALGORITHM)


async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Security(HTTPBearer()),
        token_fact: TokenFactory = Depends(get_token_factory),
        user_repo: UserRepository = Depends(get_user_repo)
) -> UserEntity:
    token = credentials.credentials
    user = await auth_case(token, token_fact, user_repo)
    return user