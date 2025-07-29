import logging
from typing import Any, Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session

from config.config import Settings

LOGGER = logging.getLogger(__name__)


@as_declarative()
class Base:
    id: Any
    __name__: str

    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()


engine = None
session_maker = None


def _get_db(db_connect_string: str, display_sql_statements: bool = False) -> Session:
    global engine
    global session_maker

    if not engine:
        LOGGER.warning("Creating Engine . . .")
        # for sqlite, we would need this:
        # connect_args = {"check_same_thread": False}
        # engine = create_engine(db_connect_string, echo=False, connect_args=connect_args)
        engine = create_engine(db_connect_string, pool_pre_ping=True, echo=display_sql_statements)

    if not session_maker:
        LOGGER.warning("Creating session maker . . .")
        session_maker = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    return session_maker()


def get_db() -> Generator:
    settings = Settings()
    database_url = settings.DATABASE_URL
    display_sql_statements = settings.DISPLAY_SQL_STATEMENTS

    db = None
    try:
        db = _get_db(db_connect_string=database_url, display_sql_statements=display_sql_statements)
        yield db
    finally:
        if db:
            db.close()


def get_db_with_connect_string(
    db_connect_string: str, display_sql_statements: bool = False
) -> Session:

    db = None
    try:
        db = _get_db(
            db_connect_string=db_connect_string, display_sql_statements=display_sql_statements
        )
        yield db
    finally:
        if db:
            db.close()


if __name__ == "__main__":
    my_db = next(get_db_with_connect_string(db_connect_string="sqlite://"))
    print(my_db.get_bind())

    my_db = next(get_db())
    print(my_db.get_bind())
