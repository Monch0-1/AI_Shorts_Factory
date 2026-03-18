from sqlmodel import SQLModel
from CreateShorts.database import engine
# Important: Import models so SQLModel metadata knows about them
from CreateShorts.Models.database_models import SFXLibrary

def reset_database():
    print("--- Resetting Database ---")
    print("Dropping all tables...")
    SQLModel.metadata.drop_all(engine)
    print("Creating all tables with new schema...")
    SQLModel.metadata.create_all(engine)
    print("Database reset successful.")

if __name__ == "__main__":
    reset_database()
