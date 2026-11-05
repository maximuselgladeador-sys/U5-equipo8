import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.domain import Order
from src.repository import OrderRow, SqlOrderRepository, make_engine


def _count(session):
    return session.scalar(select(func.count()).select_from(OrderRow))


def test_repository_commit():
    engine = make_engine()
    with Session(engine) as session:
        SqlOrderRepository(session).save(1, Order(120))
        session.commit()
        assert session.scalar(select(OrderRow).where(OrderRow.id == 1)).total == 120


def test_repository_rollback():
    engine = make_engine()
    with Session(engine) as session:
        SqlOrderRepository(session).save(1, Order(120))
        session.rollback()
        assert session.scalar(select(OrderRow).where(OrderRow.id == 1)) is None


def test_save_order_250_with_id_2():  # actividad E4
    engine = make_engine()
    with Session(engine) as session:
        repo = SqlOrderRepository(session)
        repo.save(2, Order(250))
        repo.commit()
        row = repo.get(2)
        assert (row.id, row.total, row.status) == (2, 250, "NEW")


def test_commit_persists_across_sessions():
    engine = make_engine("sqlite+pysqlite:///:memory:")
    with Session(engine) as s1:
        repo = SqlOrderRepository(s1)
        repo.save(1, Order(120))
        repo.commit()
    with Session(engine) as s2:
        assert SqlOrderRepository(s2).get(1).total == 120


def test_repository_rollback_method():
    engine = make_engine()
    with Session(engine) as session:
        repo = SqlOrderRepository(session)
        repo.save(1, Order(120))
        repo.rollback()
        assert repo.get(1) is None


def test_duplicate_id_violates_uniqueness_and_rolls_back():
    engine = make_engine()
    with Session(engine) as session:
        repo = SqlOrderRepository(session)
        repo.save(1, Order(100))
        repo.commit()
        repo.save(1, Order(999))  # mismo id
        with pytest.raises(IntegrityError):
            repo.commit()
        assert _count(session) == 1
        assert repo.get(1).total == 100  # el original no se alteró


def test_saves_confirmed_status():
    engine = make_engine()
    order = Order(100)
    order.confirm()
    with Session(engine) as session:
        repo = SqlOrderRepository(session)
        repo.save(5, order)
        repo.commit()
        assert repo.get(5).status == "CONFIRMED"


def test_get_missing_returns_none():
    with Session(make_engine()) as session:
        assert SqlOrderRepository(session).get(404) is None
