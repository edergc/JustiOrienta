from sqlalchemy import Column, ForeignKey, Integer, String, event
from sqlalchemy.orm import relationship

from app.models.base import Base, normalizar


class Alias(Base):
    __tablename__ = "alias"

    id = Column(Integer, primary_key=True, index=True)
    dependencia_id = Column(Integer, ForeignKey("dependencias.id"), nullable=False, index=True)
    alias = Column(String(200), nullable=False)
    alias_normalizado = Column(String(200), index=True)

    dependencia = relationship("Dependencia", back_populates="alias")

    def __repr__(self):
        return f"<Alias {self.alias}>"


@event.listens_for(Alias, "before_insert")
@event.listens_for(Alias, "before_update")
def _normalizar_alias(mapper, connection, target):
    target.alias_normalizado = normalizar(target.alias)
