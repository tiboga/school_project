import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.orm import Session
SqlAlchemyBase = orm.declarative_base()

__factory = None


def global_init():
    global __factory
    if __factory:
        return

    conn_str = sa.engine.URL.create(
        drivername='postgresql',
        username='postgres',
        host='127.0.0.1',
        database='school_project',
        password='postgres',
    )

    engine = sa.create_engine(conn_str, echo=False)
    __factory = orm.sessionmaker(bind=engine)

    SqlAlchemyBase.metadata.create_all(engine)


def create_session() -> Session:
    global __factory
    return __factory()
