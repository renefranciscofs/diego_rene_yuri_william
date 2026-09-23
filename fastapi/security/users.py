from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Base de usuários em memória (dict Python, não um banco de dados).
# Nota sobre injeção de SQL / SQLModel: como o acesso abaixo é um
# `dict.get(username)` — e não uma query SQL montada por concatenação de
# string — não há superfície de SQL injection aqui hoje. Quando esta
# base for substituída por persistência real (ver README/SECURITY.md),
# use SQLModel com queries parametrizadas via `session.exec(select(User)
# .where(User.username == username))`, nunca SQL cru com f-string/`%`.
_FAKE_USERS_DB = {
    "admin": {
        "username": "admin",
        "hashed_password": pwd_context.hash("admin123"),
    },
}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def authenticate_user(username: str, password: str) -> dict | None:
    user = _FAKE_USERS_DB.get(username)
    if not user or not verify_password(password, user["hashed_password"]):
        return None
    return user


def get_user(username: str) -> dict | None:
    return _FAKE_USERS_DB.get(username)
