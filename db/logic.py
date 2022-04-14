from typing import Any
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, Session
from models import User, Base


class CoreDatabase:
    def __init__(self, echo: bool = False) -> None:
        self._engine = create_engine("sqlite:///users.db", echo=echo)
        self._metadata = MetaData()
        self._metadata.reflect(self._engine)
        self._session = sessionmaker(bind=self._engine)

    @property
    def session(self) -> Session:
        return self._session()


class Database(CoreDatabase):
    def __init__(self) -> None:
        super().__init__()
        Base.metadata.create_all(self._engine)

    def create_user(self, user_id: int):
        with self.session as session:
            if session.query(User).get(user_id) is None:
                user = User(id=user_id)
                session.add(user)
                session.commit()

    def set_param(self, user_id: int, param_type: str, param: Any):
        with self.session as session:
            session.query(User).filter(User.id == user_id).update({param_type: param})
            session.commit()

    def get_params(self, user_id: int) -> dict:
        with self.session as session:
            user = session.query(User).get(user_id)
            return {
                "text": user.search_text,
                "schedule": user.schedule,
                "area": user.area,
                "salary": user.salary,
                "only_with_salary": user.only_with_salary,
                "currency": user.currency,
            }

    def delete_user(self, user_id: int):
        with self.session as session:
            user = session.query(User).get(user_id)
            session.delete(user)
            session.commit()
