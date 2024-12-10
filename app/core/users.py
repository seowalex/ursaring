from typing import Annotated

from fastapi import Depends
from fastapi_users import BaseUserManager, FastAPIUsers, IntegerIDMixin
from fastapi_users.db import SQLAlchemyUserDatabase

from .auth import auth_backend
from .db import User, get_user_db


class UserManager(IntegerIDMixin, BaseUserManager[User, int]):
    pass


async def get_user_manager(
    user_db: Annotated[SQLAlchemyUserDatabase, Depends(get_user_db)],
):
    yield UserManager(user_db)


fastapi_users = FastAPIUsers[User, int](get_user_manager, [auth_backend])
get_current_user = fastapi_users.current_user()
