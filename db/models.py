from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
)


Base = declarative_base()


class User(Base):
    __tablename__ = "Users"

    id = Column(Integer, primary_key=True)
    schedule = Column(String)
    area = Column(Integer)
    salary = Column(Integer)
    only_with_salary = Column(Boolean)
    currency = Column(String)
