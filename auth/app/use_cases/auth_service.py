import uuid
from secrets import compare_digest

from app.entities.token import AccessTokenEntity, TokenEntity, RefreshTokenEntity
from app.entities.user import UserEntity
from app.exceptions import InvalidTokenError, AuthorizationError, RegistrationError
from app.framework.factory import TokenFactory
from app.framework.repository import UserRepository, TokenRepository


async def register_case(username: str, password: str, confirm_password, user_repo: UserRepository):
    """Аутентификация пользователя, проверка введенных данных исходя из строчки в бд"""
    if not compare_digest(password, confirm_password):
        raise RegistrationError("Passwords don't match")
    existing_user = await user_repo.get_by_username(username)
    if existing_user:
        raise RegistrationError(f"User {username} already exist")
    hashed_password = UserEntity.hash_password(password)
    return await user_repo.create(username, hashed_password)


async def login_case(
        username: str, password: str,
        user_repo: UserRepository,
        token_repo: TokenRepository,
        token_fact: TokenFactory) -> dict:
    """Сценарий авторизации пользователя"""
    user = await user_repo.get_by_username(username)
    if not user or not user.verify_password(password):
        raise AuthorizationError(extra="Invalid username or password")
    jti: str = str(uuid.uuid4())
    access: AccessTokenEntity = await create_token_case('access', token_fact, user.id, jti=jti)
    refresh: RefreshTokenEntity = await create_token_case('refresh', token_fact, user.id, jti=jti)
    await token_repo.save_refresh(refresh, refresh.ttl, user.id)
    tokens = {
        "access": access.value,
        "refresh": refresh.value,
    }
    return tokens


async def refresh_case(
        old_refresh: str,
        token_repo: TokenRepository,
        token_fact: TokenFactory
) -> dict:
    """Создание новых токенов, бан старого refresh token"""
    if user := await token_repo.get_user_by_refresh(old_refresh):
        access: AccessTokenEntity = await create_token_case('access', token_fact, user.id)
        refresh: RefreshTokenEntity = await create_token_case('refresh', token_fact, user.id)
        await token_repo.save_refresh(refresh, refresh.ttl, user.id)
        await token_repo.drop_refresh(old_refresh)
        return {"access": access.value, "refresh": refresh.value}
    else:
        raise InvalidTokenError("Refresh token not exist or token already been used")


async def auth_case(access: str, token_fact: TokenFactory, user_repo: UserRepository) -> UserEntity:
    """Вернуть пользователя по его access token"""
    token: AccessTokenEntity = await token_fact.decode_token(access)
    user = await user_repo.get_by_id(token.user_id)
    if not user:
        raise InvalidTokenError("Username with this token not exist")
    return user


async def create_token_case(
        token_type: str, token_factory: TokenFactory, user_id: int = None, jti: str = None) -> TokenEntity:
    """Создание JWT токена, кодирование данных
    :arg token_type: тип токена - access/refresh
    :arg data: данные, которые будут вшиты в токен"""
    token = await token_factory.create_token(token_type, user_id, jti=jti)
    return token