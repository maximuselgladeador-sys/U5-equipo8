"""Pruebas parametrizadas con los datos didácticos de data/*.csv."""
import csv
from pathlib import Path

import pytest

from src.domain import CustomerHasDebt, Order

DATA = Path(__file__).resolve().parent.parent / "data"

# Resultado esperado por escenario (CP08 actualizado tras el ciclo TDD).
EXPECTED = {
    1: 120.00, 2: 170.00, 3: CustomerHasDebt, 4: ValueError, 5: ValueError,
    6: 850.00, 7: 0.01, 8: ValueError, 9: 255.00, 10: 75.00,
    11: CustomerHasDebt, 12: 84.99,
}


def load_orders():
    with (DATA / "pedidos_prueba.csv").open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


@pytest.mark.parametrize("row", load_orders(), ids=lambda r: f"CP{int(r['pedido_id']):02d}")
def test_csv_order_scenarios(row):
    order = Order(
        float(row["total"]),
        vip=row["es_vip"] == "1",
        customer_debt=float(row["deuda_cliente"]),
        status=row["estado_inicial"],
    )
    expected = EXPECTED[int(row["pedido_id"])]
    if isinstance(expected, type):
        with pytest.raises(expected):
            order.confirm()
        assert order.status == row["estado_inicial"]  # no cambia ante error
    else:
        assert order.confirm() == pytest.approx(expected)
        assert order.status == "CONFIRMED"
