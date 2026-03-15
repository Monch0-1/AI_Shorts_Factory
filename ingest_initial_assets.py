from CreateShorts.database import init_db, engine
from CreateShorts.Models.database_models import SFXLibrary
from sqlmodel import Session


def ingest_samples():
    # 1. Asegurar que las tablas existan
    init_db()

    with Session(engine) as session:
        # 2. Crear el objeto (Como un new Entity() en Java)
        sample_sfx = SFXLibrary(
            category="horror",
            intent_tag="fahh",
            sfx_name="The Classic FAHHH",
            file_path="resources/audio/sfx/fahh_original.mp3",
            description="Usually funny soundusen in initial mocks"
        )

        # 3. Guardar (session.persist / session.save)
        try:
            session.add(sample_sfx)
            session.commit()
            print("✅ Sonido FAHHH registrado exitosamente en Postgres.")
        except Exception as e:
            session.rollback()
            print(f"❌ Error al registrar (posiblemente ya existe): {e}")


if __name__ == "__main__":
    ingest_samples()