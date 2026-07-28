"""ORM models for the Kimball star schema (public schema)."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    CHAR,
    Boolean,
    Date,
    DateTime,
    ForeignKeyConstraint,
    Identity,
    Integer,
    Numeric,
    PrimaryKeyConstraint,
    String,
    Text,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class DDate(Base):
    __tablename__ = "d_date"

    date_sk: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    day: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    month_name: Mapped[str | None] = mapped_column(String(20))
    quarter: Mapped[int] = mapped_column(Integer, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    week_day: Mapped[str | None] = mapped_column(String(20))
    is_weekend: Mapped[bool | None] = mapped_column(Boolean, server_default=text("FALSE"))


class DCustomer(Base):
    __tablename__ = "d_customer"

    customer_sk: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[str | None] = mapped_column(String(50))
    customer_name: Mapped[str | None] = mapped_column(String(100))
    segment: Mapped[str | None] = mapped_column(String(50))
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)
    expiration_date: Mapped[date | None] = mapped_column(Date)
    current_flag: Mapped[str | None] = mapped_column(CHAR(1), server_default=text("'Y'"))


class DProduct(Base):
    __tablename__ = "d_product"

    product_sk: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[str | None] = mapped_column(String(50))
    product_name: Mapped[str | None] = mapped_column(String(200))
    category: Mapped[str | None] = mapped_column(String(50))
    sub_category: Mapped[str | None] = mapped_column(String(50))
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)
    expiration_date: Mapped[date | None] = mapped_column(Date)
    current_flag: Mapped[str | None] = mapped_column(CHAR(1), server_default=text("'Y'"))


class DLocation(Base):
    __tablename__ = "d_location"

    location_sk: Mapped[int] = mapped_column(Integer, primary_key=True)
    country: Mapped[str | None] = mapped_column(String(50))
    region: Mapped[str | None] = mapped_column(String(50))
    state: Mapped[str | None] = mapped_column(String(50))
    city: Mapped[str | None] = mapped_column(String(100))
    postal_code: Mapped[str | None] = mapped_column(String(20))


class DOrder(Base):
    __tablename__ = "d_order"

    order_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    ship_mode: Mapped[str | None] = mapped_column(String(50))


class DSegment(Base):
    __tablename__ = "d_segment"

    segment_sk: Mapped[int] = mapped_column(Integer, primary_key=True)
    segment_name: Mapped[str | None] = mapped_column(String(50), unique=True)


class FSales(Base):
    __tablename__ = "f_sales"

    __table_args__ = (
        ForeignKeyConstraint(["order_date_sk"], ["d_date.date_sk"]),
        ForeignKeyConstraint(["ship_date_sk"], ["d_date.date_sk"]),
        ForeignKeyConstraint(["customer_sk"], ["d_customer.customer_sk"]),
        ForeignKeyConstraint(["product_sk"], ["d_product.product_sk"]),
        ForeignKeyConstraint(["location_sk"], ["d_location.location_sk"]),
        ForeignKeyConstraint(["order_id"], ["d_order.order_id"]),
        PrimaryKeyConstraint(
            "order_date_sk", "customer_sk", "product_sk", "location_sk",
            name="pk_f_sales",
        ),
    )

    order_date_sk: Mapped[int] = mapped_column(Integer, nullable=False)
    ship_date_sk: Mapped[int] = mapped_column(Integer, nullable=False)
    customer_sk: Mapped[int] = mapped_column(Integer, nullable=False)
    product_sk: Mapped[int] = mapped_column(Integer, nullable=False)
    location_sk: Mapped[int] = mapped_column(Integer, nullable=False)
    order_id: Mapped[str | None] = mapped_column(String(50))
    ship_mode: Mapped[str | None] = mapped_column(String(50))
    sales: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    quantity: Mapped[int | None] = mapped_column(Integer)
    discount: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    profit: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))


class EtlLog(Base):
    __tablename__ = "etl_log"

    log_id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True)
    run_date: Mapped[datetime | None] = mapped_column(DateTime, server_default=text("NOW()"))
    step: Mapped[str | None] = mapped_column(String(50))
    rows_affected: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str | None] = mapped_column(String(20))
    message: Mapped[str | None] = mapped_column(Text)
    duration_sec: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
