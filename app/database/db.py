from contextlib import contextmanager
from .models import SessionLocal, init_db

def initialize_database():
    init_db()

@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
