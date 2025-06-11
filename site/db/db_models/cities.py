import sqlalchemy
from .db_session import SqlAlchemyBase


class Cities(SqlAlchemyBase):
    __tablename__ = 'cities'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.Text)
    population = sqlalchemy.Column(sqlalchemy.Integer)
