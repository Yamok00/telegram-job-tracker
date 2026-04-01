from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone

from config import settings

Base = declarative_base()

class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    company = Column(String, index=True, nullable=False)
    role = Column(String, index=True, nullable=False)
    status = Column(String, default="Applied") # Applied, Assessment, Interview, Offer, Rejected, Update
    expertise_level = Column(String, default="Generalist") # Expert, Generalist
    last_update_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    emails = relationship("EmailReference", back_populates="application")

    @property
    def days_since_update(self):
        delta = datetime.now(timezone.utc) - self.last_update_date.replace(tzinfo=timezone.utc)
        return delta.days

class EmailReference(Base):
    __tablename__ = "email_references"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(String, unique=True, index=True, nullable=False)
    thread_id = Column(String, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"))
    date_received = Column(DateTime)
    subject = Column(String)

    application = relationship("Application", back_populates="emails")

engine = create_engine(
    settings.database_url, connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
