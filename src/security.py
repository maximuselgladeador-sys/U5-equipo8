"""Política de autorización para cancelar pedidos."""
from datetime import UTC, datetime, timedelta


def can_cancel(status, owner_id, user_id, is_admin, created_at, now=None):
    """Un pedido SHIPPED nunca se cancela (ni por admin). Admin cancela el resto.

    Un usuario normal solo cancela lo propio, durante < 24 h desde created_at.
    `now` se inyecta en las pruebas para evitar resultados variables.
    """
    now = now or datetime.now(UTC)
    if status == "SHIPPED":
        return False
    if is_admin:
        return True
    return owner_id == user_id and now - created_at < timedelta(hours=24)
