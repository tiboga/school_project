import sqlalchemy
from sqlalchemy import DateTime
from .db_session import SqlAlchemyBase
from datetime import datetime


class Tasks(SqlAlchemyBase):
    __tablename__ = 'tasks'
    id = sqlalchemy.Column(
        sqlalchemy.Integer,
        primary_key=True
    )
    coord_1 = sqlalchemy.Column(
        sqlalchemy.types.Float
    )
    coord_2 = sqlalchemy.Column(
        sqlalchemy.types.Float
    )
    note = sqlalchemy.Column(
        sqlalchemy.types.String
    )
    ended = sqlalchemy.Column(
        sqlalchemy.types.Boolean
    )
    created_on = sqlalchemy.Column(
        DateTime(),
        default=datetime.now)
    user_id = sqlalchemy.Column(
        sqlalchemy.types.Integer,
        sqlalchemy.ForeignKey('users.id')
    )
    volunteer_id = sqlalchemy.Column(
        sqlalchemy.types.Integer,
        sqlalchemy.ForeignKey('users.id')
    )
    picture_before = sqlalchemy.Column(
        sqlalchemy.types.String
    )
    picture_after = sqlalchemy.Column(
        sqlalchemy.types.String
    )
    cost = sqlalchemy.Column(
        sqlalchemy.types.Integer
    )
    status = sqlalchemy.Column(
        sqlalchemy.types.String
    )
