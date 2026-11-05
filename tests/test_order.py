import pytest

from src.domain import CustomerHasDebt, Order


# --- Éxito -------------------------------------------------------------
def test_vip_discount():
    o = Order(100, vip=True)
    assert o.confirm() == 85
    assert o.status == "CONFIRMED"
    assert o.discount == 15


def test_regular_no_discount():
    o = Order(100)
    assert o.confirm() == 100
    assert o.discount == 0.0


def test_vip_200_charges_170():
    assert Order(200, vip=True).confirm() == 170


def test_regular_200_charges_200():
    assert Order(200).confirm() == 200


def test_debt_as_entity_attribute_zero_allows_confirmation():
    assert Order(100, customer_debt=0).confirm() == 100


# --- Error -------------------------------------------------------------
def test_customer_debt_parameter():
    with pytest.raises(CustomerHasDebt):
        Order(100).confirm(customer_debt=50)


def test_customer_debt_attribute():
    with pytest.raises(CustomerHasDebt):
        Order(100, customer_debt=500).confirm()


def test_debt_does_not_change_status():
    o = Order(100, customer_debt=1)
    with pytest.raises(CustomerHasDebt):
        o.confirm()
    assert o.status == "NEW"


@pytest.mark.parametrize("total", [0, -1, -0.01])
def test_invalid_total(total):
    with pytest.raises(ValueError, match="positive"):
        Order(total).confirm()


# --- Límite ------------------------------------------------------------
def test_minimum_positive_total_vip():
    assert Order(0.01, vip=True).confirm() == 0.01  # descuento redondea a 0.00


def test_vip_rounding_99_99():
    assert Order(99.99, vip=True).confirm() == pytest.approx(84.99)


def test_debt_of_one_cent_blocks():
    with pytest.raises(CustomerHasDebt):
        Order(100).confirm(customer_debt=0.01)


# --- TDD: confirmación doble ------------------------------------------
def test_cannot_confirm_twice():
    order = Order(100)
    order.confirm()
    with pytest.raises(ValueError, match="already confirmed"):
        order.confirm()


def test_double_confirm_keeps_discount_unchanged():
    order = Order(100, vip=True)
    order.confirm()
    with pytest.raises(ValueError):
        order.confirm()
    assert order.discount == 15
