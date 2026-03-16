from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class SFXLibrary(SQLModel, table=True):
    __tablename__ = "sfx_library"

    id: Optional[int] = Field(default=None, primary_key=True)
    category: str = Field(index=True)      # e.g., 'horror', 'comedy'
    intent_tag: str = Field(index=True)    # e.g., 'scare', 'laugh', 'fahh'
    sfx_name: str                          # Nombre descriptivo
    file_path: str = Field(unique=True)    # Ruta al archivo local
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)