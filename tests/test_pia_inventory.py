"""Matriz PIA (9 casos): reglas de inventario de 'Tornillos del Norte'."""
from unittest.mock import Mock

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.inventory import InsufficientStock, Product
from src.inventory_service import ReservationRow, ReservationService
from src.repository import make_engine


def gateway(result=True):
    g = Mock()
    g.charge.return_value = result
    return g


def count(session):
    return session.scalar(select(func.count()).select_from(ReservationRow))


# R1 · Reserva de stock
def test_pia_01_reserve_success():
    p = Product("TOR-1", stock=5, unit_price=10)
    p.reserve(2)
    assert p.stock == 3


@pytest.mark.parametrize("qty", [-1, 0])
def test_pia_02_invalid_quantity(qty):
    with pytest.raises(ValueError):
        Product("TOR-1", 5, 10).reserve(qty)


def test_pia_03_limit_reserve_all_then_one_more():
    p = Product("TOR-1", stock=5, unit_price=10)
    p.reserve(5)
    assert p.stock == 0
    with pytest.raises(InsufficientStock):
        p.reserve(1)


# R2 · Precio de mayoreo (>= 50 piezas, -10%)
def test_pia_04_wholesale_discount():
    assert Product("TOR-1", 100, 10).line_total(60) == 540.00


def test_pia_05_zero_quantity_invoice_rejected():
    with pytest.raises(ValueError):
        Product("TOR-1", 100, 10).line_total(0)


def test_pia_06_limit_49_vs_50_pieces():
    p = Product("TOR-1", 100, 10)
    assert p.line_total(49) == 490.00
    assert p.line_total(50) == 450.00


# R3 · Cobro + persistencia con compensación
def test_pia_07_mock_approved_persists_reservation():  # mock + persistencia
    g, product = gateway(True), Product("TOR-1", 10, 20)
    with Session(make_engine()) as s:
        assert ReservationService(g, s).reserve_and_pay(1, product, 2) == 40
        g.charge.assert_called_once_with(40)
        assert s.get(ReservationRow, 1).qty == 2
    assert product.stock == 8


def test_pia_08_mock_rejected_restores_stock_and_saves_nothing():
    g, product = gateway(False), Product("TOR-1", 10, 20)
    with Session(make_engine()) as s:
        with pytest.raises(RuntimeError, match="payment rejected"):
            ReservationService(g, s).reserve_and_pay(1, product, 2)
        assert count(s) == 0
    assert product.stock == 10


def test_pia_09_limit_gateway_timeout_restores_stock():
    g = Mock()
    g.charge.side_effect = TimeoutError("timeout")
    product = Product("TOR-1", 2, 20)
    with Session(make_engine()) as s:
        with pytest.raises(TimeoutError):
            ReservationService(g, s).reserve_and_pay(1, product, 2)  # qty == stock
        assert count(s) == 0
    assert product.stock == 2
