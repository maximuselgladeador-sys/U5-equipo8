"""Servicio de reservas: stock + pasarela de pago (mock) + persistencia (SQLAlchemy)."""
from sqlalchemy import Column, Float, Integer, String
from sqlalchemy.orm import Session

from src.repository import Base


class ReservationRow(Base):
    __tablename__ = "reservations"
    id = Column(Integer, primary_key=True)
    sku = Column(String, nullable=False)
    qty = Column(Integer, nullable=False)
    total = Column(Float, nullable=False)


class ReservationService:
    def __init__(self, gateway, session: Session):
        self.gateway = gateway
        self.session = session

    def reserve_and_pay(self, reservation_id, product, qty):
        """Reserva stock, cobra y persiste. Ante cualquier fallo compensa el stock
        y hace rollback, evitando el estado inconsistente descrito en E5."""
        total = product.line_total(qty)
        product.reserve(qty)
        try:
            if not self.gateway.charge(total):
                raise RuntimeError("payment rejected")
            self.session.add(ReservationRow(id=reservation_id, sku=product.sku, qty=qty, total=total))
            self.session.commit()
        except Exception:
            product.release(qty)
            self.session.rollback()
            raise
        return total
