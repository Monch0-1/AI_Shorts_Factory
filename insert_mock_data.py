from CreateShorts.database import init_db, engine
from CreateShorts.Models.database_models import SFXLibrary
from sqlmodel import Session


def insert_mock_data():
    # 1. Asegurar que las tablas existan
    init_db()

    mocks = [
        SFXLibrary(
            category="horror",
            intent_tag="whisper",
            sfx_name="Ghost Whisper",
            file_path="resources/sfx/ghost_whisper.mp3",
            description="Spooky whisper sound"
        ),
        SFXLibrary(
            category="horror",
            intent_tag="hit",
            sfx_name="Scary Hit",
            file_path="resources/sfx/scary_hit.mp3",
            description="Jump scare hit sound"
        ),
        SFXLibrary(
            category="comedy",
            intent_tag="laugh",
            sfx_name="Audience Laugh",
            file_path="resources/sfx/audience_laugh.mp3",
            description="Standard sitcom laugh track"
        ),
        SFXLibrary(
            category="comedy",
            intent_tag="ba-dum-tss",
            sfx_name="Drum Fill",
            file_path="resources/sfx/drum_fill.mp3",
            description="Classic ba-dum-tss after a joke"
        )
    ]

    with Session(engine) as session:
        for mock in mocks:
            try:
                session.add(mock)
                session.commit()
                print(f"✅ Sonido '{mock.sfx_name}' registrado.")
            except Exception as e:
                session.rollback()
                print(f"❌ Error al registrar '{mock.sfx_name}': El registro ya existe o hay un error.")

if __name__ == "__main__":
    insert_mock_data()
