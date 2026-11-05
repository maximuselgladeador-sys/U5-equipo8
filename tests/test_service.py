from unittest.mock import Mock

import pytest

from src.application import OrderService
from src.domain import CustomerHasDebt, Order


def make_gateway(result):
    gateway = Mock()
    gateway.charge.return_value = result
    return gateway


def test_gateway_approved():
    gateway = make_gateway(True)
    assert OrderService(gateway).checkout(Order(100)) == 100
    gateway.charge.assert_called_once_with(100)


def test_gateway_rejected():
    gateway = make_gateway(False)
    with pytest.raises(RuntimeError, match="payment rejected"):
        OrderService(gateway).checkout(Order(100))
    gateway.charge.assert_called_once_with(100)


def test_vip_approved_charges_discounted_amount():
    gateway = make_gateway(True)
    assert OrderService(gateway).checkout(Order(200, vip=True)) == 170
    gateway.charge.assert_called_once_with(170)


def test_vip_rejected_attempts_170_and_raises():  # actividad E5
    gateway = make_gateway(False)
    with pytest.raises(RuntimeError, match="payment rejected"):
        OrderService(gateway).checkout(Order(200, vip=True))
    gateway.charge.assert_called_once_with(170)


def test_invalid_order_never_reaches_gateway():
    gateway = make_gateway(True)
    with pytest.raises(ValueError):
        OrderService(gateway).checkout(Order(0))
    gateway.charge.assert_not_called()


def test_debtor_never_reaches_gateway():
    gateway = make_gateway(True)
    with pytest.raises(CustomerHasDebt):
        OrderService(gateway).checkout(Order(100, customer_debt=10))
    gateway.charge.assert_not_called()


def test_gateway_timeout_propagates():
    gateway = Mock()
    gateway.charge.side_effect = TimeoutError("gateway timeout")
    with pytest.raises(TimeoutError):
        OrderService(gateway).checkout(Order(100))


# --- Análisis de consistencia (E5) -------------------------------------
def test_RISK_rejected_payment_leaves_order_confirmed():
    """Caracteriza el defecto conocido: pedido CONFIRMED aunque el pago falló.

    Si en el futuro se corrige el servicio (confirmar solo tras cobro exitoso),
    esta prueba debe invertirse: assert order.status == "NEW".
    """
    order = Order(100)
    with pytest.raises(RuntimeError):
        OrderService(make_gateway(False)).checkout(order)
    assert order.status == "CONFIRMED"  # inconsistencia documentada


def test_RISK_retry_after_rejection_is_blocked():
    """Consecuencia directa: el reintento de pago falla por 'already confirmed'."""
    order = Order(100)
    with pytest.raises(RuntimeError):
        OrderService(make_gateway(False)).checkout(order)
    with pytest.raises(ValueError, match="already confirmed"):
        OrderService(make_gateway(True)).checkout(order)
