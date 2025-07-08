from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel
from sqlalchemy import func


class BaseModel(SQLModel):
    """Базовая модель с общими полями"""
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={
            "nullable": False,
            "default": func.now()
        }
    )
    updated_at: Optional[datetime] = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={
            "nullable": True,
            "onupdate": func.now()
        }
    )
    is_deleted: bool = Field(default=False)
