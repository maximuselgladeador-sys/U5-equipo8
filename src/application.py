"""Servicio de aplicación. Depende del puerto PaymentGateway, no de un proveedor."""
from typing import Protocol


class PaymentGateway(Protocol):
    def charge(self, amount: float) -> bool: ...


class OrderService:
    def __init__(self, gateway: PaymentGateway):
        self.gateway = gateway

    def checkout(self, order):
        # RIESGO CONOCIDO (ver E5): confirm() cambia el estado ANTES del cobro.
        amount = order.confirm()
        if not self.gateway.charge(amount):
            raise RuntimeError("payment rejected")
        return amount
