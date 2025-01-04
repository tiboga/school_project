import datetime
import logging
import os, sys
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))
import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.orm import Session
import sqlalchemy.ext.declarative as dec

SqlAlchemyBase = orm.declarative_base()

__factory = None


def global_init():
    global __factory
    if __factory:
        return

    conn_str = sa.URL.create(
                        drivername="postgresql",
                        username="tibo",
                        host="127.0.0.1",
                        database="school_project",
                        password='1d4a5f3s'
                    )

    engine = sa.create_engine(conn_str, echo=False)
    __factory = orm.sessionmaker(bind=engine)

    from . import __all_models

    SqlAlchemyBase.metadata.create_all(engine)


def create_session() -> Session:
    global __factory
    return __factory()
    