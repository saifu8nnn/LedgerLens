import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Fetch the database URL from the .env file.
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://admin:securepass@127.0.0.1:5432/ledgerlens"
)

# Create the SQLAlchemy engine to manage the connection pool to PostgreSQL
engine = create_engine(DATABASE_URL)

# Create a configured "Session" class. Each instance of this class will be a database session.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a declarative base class. All our ORM models will inherit from this class.
Base = declarative_base()

# Dependency generator to be used in FastAPI endpoints.
# This ensures a database session is opened for each request and cleanly closed afterward.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()