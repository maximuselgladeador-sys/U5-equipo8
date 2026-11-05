from datetime import UTC, datetime, timedelta

import pytest

from src.security import can_cancel

NOW = datetime(2026, 11, 5, 12, 0, tzinfo=UTC)  # fecha fija inyectada


def test_owner_within_24h():
    assert can_cancel("NEW", 1, 1, False, NOW - timedelta(hours=1), NOW)


def test_stranger_denied():
    assert not can_cancel("NEW", 1, 2, False, NOW, NOW)


def test_shipped_denied_even_admin():
    assert not can_cancel("SHIPPED", 1, 1, True, NOW, NOW)


def test_expired_denied():
    assert not can_cancel("NEW", 1, 1, False, NOW - timedelta(hours=25), NOW)


def test_admin_cancels_other_users_new_order():  # actividad E6
    assert can_cancel("NEW", 1, 99, True, NOW - timedelta(days=10), NOW)


def test_admin_cancels_pending():
    assert can_cancel("PENDING", 1, 99, True, NOW, NOW)


def test_owner_exactly_24h_denied():  # límite: < 24h estricto
    assert not can_cancel("NEW", 1, 1, False, NOW - timedelta(hours=24), NOW)


def test_owner_just_before_24h_allowed():
    created = NOW - timedelta(hours=23, minutes=59, seconds=59)
    assert can_cancel("NEW", 1, 1, False, created, NOW)


def test_owner_shipped_denied():
    assert not can_cancel("SHIPPED", 1, 1, False, NOW, NOW)


def test_default_now_uses_current_time():
    created = datetime.now(UTC) - timedelta(minutes=5)
    assert can_cancel("NEW", 1, 1, False, created)


@pytest.mark.parametrize(
    "is_admin,owner,status,hours,expected",
    [
        (False, True, "NEW", 2, True),
        (False, False, "NEW", 2, False),
        (True, False, "NEW", 500, True),
        (True, False, "SHIPPED", 1, False),
        (False, True, "PENDING", 24, False),
    ],
)
def test_authorization_matrix(is_admin, owner, status, hours, expected):
    user_id = 1 if owner else 2
    created = NOW - timedelta(hours=hours)
    assert can_cancel(status, 1, user_id, is_admin, created, NOW) is expected
