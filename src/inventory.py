"""PIA ficticio: Ferretería 'Tornillos del Norte'. Dominio de inventario (sin ORM)."""
from dataclasses import dataclass

WHOLESALE_MIN_QTY = 50
WHOLESALE_RATE = 0.10


class InsufficientStock(Exception):
    """No hay existencias suficientes para la reserva."""


@dataclass
class Product:
    sku: str
    stock: int
    unit_price: float

    def reserve(self, qty):
        if qty <= 0:
            raise ValueError("quantity must be positive")
        if qty > self.stock:
            raise InsufficientStock(f"requested {qty}, available {self.stock}")
        self.stock -= qty

    def release(self, qty):
        self.stock += qty

    def line_total(self, qty):
        """Importe de la línea; mayoreo (>= 50 piezas) recibe 10% de descuento."""
        if qty <= 0:
            raise ValueError("quantity must be positive")
        total = self.unit_price * qty
        if qty >= WHOLESALE_MIN_QTY:
            total *= 1 - WHOLESALE_RATE
        return round(total, 2)
