from CreateShorts.database import init_db, engine
from CreateShorts.Models.database_models import SFXLibrary
from sqlmodel import Session


def insert_mock_data():
    # 1. Asegurar que las tablas existan
    init_db()

    mocks_final = [
        # Horror Category
        SFXLibrary(category="horror", intent_tag="whisper", sfx_name="Ghost Whisper", file_path="resources/sfx/ghost_whisper.mp3"),
        SFXLibrary(category="horror", intent_tag="hit", sfx_name="Scary Hit", file_path="resources/sfx/scary_hit.mp3"),
        SFXLibrary(category="horror", intent_tag="jump_scare", sfx_name="Jump Scare 1", file_path="resources/sfx/jumpscare1.mp3"),
        SFXLibrary(category="horror", intent_tag="jump_scare", sfx_name="Jump Scare 2", file_path="resources/sfx/jumpscare2.mp3"),
        
        # Comedy Category
        SFXLibrary(category="comedy", intent_tag="laugh", sfx_name="Audience Laugh", file_path="resources/sfx/Audience Laugh.mp3"),
        SFXLibrary(category="comedy", intent_tag="punchline", sfx_name="Ba Dum Tss", file_path="resources/sfx/ba-dum-tss.mp3"),
        SFXLibrary(category="comedy", intent_tag="funny_mistake", sfx_name="FAHHH", file_path="resources/sfx/fahhh_original.mp3"),
    ]

    with Session(engine) as session:
        for mock in mocks_final:
            try:
                session.add(mock)
                session.commit()
                print(f"✅ Sonido '{mock.sfx_name}' ({mock.category}/{mock.intent_tag}) registrado.")
            except Exception as e:
                session.rollback()
                print(f"❌ Error al registrar '{mock.sfx_name}': {e}")

if __name__ == "__main__":
    insert_mock_data()
