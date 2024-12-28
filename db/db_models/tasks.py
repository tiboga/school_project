import sqlalchemy
from .db_session import SqlAlchemyBase
class Tasks(SqlAlchemyBase):
    __tablename__ = "tasks"
    id = sqlalchemy.Column(sqlalchemy.Integer,primary_key=True)
    coord_1 = sqlalchemy.Column(sqlalchemy.types.Float)
    coord_2 = sqlalchemy.Column(sqlalchemy.types.Float)
    note = sqlalchemy.Column(sqlalchemy.types.String)
    ended = sqlalchemy.Column(sqlalchemy.types.Boolean)