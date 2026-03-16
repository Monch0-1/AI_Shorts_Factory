from CreateShorts.database import engine
from CreateShorts.Models.database_models import SFXLibrary
from sqlmodel import Session, select

def list_sfx():
    with Session(engine) as session:
        statement = select(SFXLibrary)
        results = session.exec(statement).all()
        print(f"Total entries in SFXLibrary: {len(results)}")
        for item in results:
            print(f"- {item.sfx_name} ({item.category}/{item.intent_tag}): {item.file_path}")

if __name__ == "__main__":
    list_sfx()
