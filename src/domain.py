"""Dominio de pedidos. No importa SQLAlchemy ni pasarelas de pago."""
from dataclasses import dataclass

VIP_RATE = 0.15


class CustomerHasDebt(Exception):
    """El cliente tiene deuda pendiente y no puede confirmar pedidos."""


@dataclass
class Order:
    total: float
    vip: bool = False
    customer_debt: float = 0.0
    status: str = "NEW"
    discount: float = 0.0

    def confirm(self, customer_debt=None):
        """Confirma el pedido y devuelve el importe a cobrar.

        `customer_debt` (opcional) sobrescribe el atributo de la entidad.
        """
        self._ensure_not_confirmed()
        if self.total <= 0:
            raise ValueError("total must be positive")
        debt = self.customer_debt if customer_debt is None else customer_debt
        if debt > 0:
            raise CustomerHasDebt("outstanding debt")
        self.discount = round(self.total * VIP_RATE, 2) if self.vip else 0.0
        self.status = "CONFIRMED"
        return self.total - self.discount

    def _ensure_not_confirmed(self):  # REFACTOR: regla extraída con nombre claro
        if self.status == "CONFIRMED":
            raise ValueError("already confirmed")
