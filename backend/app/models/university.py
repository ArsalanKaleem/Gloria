"""University domain models: Department, Program, Person, Officer."""

from datetime import datetime

from sqlalchemy import Column, String, Text, DateTime, JSON

from app.database import Base


class Department(Base):
    __tablename__ = "departments"

    id = Column(String, primary_key=True)               # e.g. "dept-cs"
    name = Column(String, nullable=False)               # "Department of Computer Science"
    description = Column(Text, nullable=True)
    programs = Column(JSON, nullable=True)              # list of program ids
    contact_email = Column(String, nullable=True)
    contact_phone = Column(String, nullable=True)
    source = Column(String, nullable=True)              # URL of the authoritative source
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Program(Base):
    __tablename__ = "programs"

    id = Column(String, primary_key=True)               # e.g. "prog-bs-cs"
    name = Column(String, nullable=False)               # "BS Computer Science"
    department = Column(String, nullable=True)          # department id
    level = Column(String, nullable=True)               # "Bachelor", "Master", "PhD"
    duration = Column(String, nullable=True)            # "4 years / 8 semesters"
    credit_hours = Column(String, nullable=True)
    admission_requirements = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    source = Column(String, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Person(Base):
    __tablename__ = "people"

    id = Column(String, primary_key=True)               # e.g. "person-jdoe"
    name = Column(String, nullable=False)
    designation = Column(String, nullable=True)         # "Professor", "HOD"
    department = Column(String, nullable=True)          # department id or name
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    specialization = Column(Text, nullable=True)
    bio = Column(Text, nullable=True)
    profile_url = Column(String, nullable=True)
    source = Column(String, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Officer(Base):
    """Senior administrators: VC, Registrar, Deans, Directors."""
    __tablename__ = "officers"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    designation = Column(String, nullable=False)
    office = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    source = Column(String, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
