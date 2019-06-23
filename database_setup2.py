import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key= True)
    name = Column(String(250), nullable = False)


class Stats(Base):
    __tablename__ = 'lifter_stats'

    id = Column(Integer, primary_key = True, autoincrement=True)
    gender = Column(String(80), nullable = False)
    weightclass = Column(String(80), nullable = False)
    clean_jerk = Column(String(80), nullable = False)
    snatch = Column(String(80), nullable = False)
    total = Column(String(80), nullable = False)
    lifter_id = Column(String(80), ForeignKey('lifter.name'))


class Lifter(Base):
    __tablename__ = 'lifter'

    id = Column(Integer, primary_key = True, autoincrement=True)
    name = Column(String(250), nullable = False)
    stats = relationship(Stats)



engine = create_engine('sqlite:///olytotalcatalog2.db')

Base.metadata.create_all(engine)
