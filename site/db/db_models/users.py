from flask_login import UserMixin
import sqlalchemy
from .db_session import SqlAlchemyBase
from werkzeug.security import generate_password_hash, check_password_hash


class Users(SqlAlchemyBase, UserMixin):
    __tablename__ = 'users'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    login = sqlalchemy.Column(sqlalchemy.Text)
    password = sqlalchemy.Column(sqlalchemy.Text)
    city = sqlalchemy.Column(sqlalchemy.Text)
    count_order_placed = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    count_order_completed = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    balance = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    contact_information = sqlalchemy.Column(sqlalchemy.Text, default="")
    fcm_token = sqlalchemy.Column(sqlalchemy.Text)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)
