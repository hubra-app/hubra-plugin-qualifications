"""Qualifications: the kinds the club tracks and who holds them.

The tables were the Guides plugin's until Guides 2.0; this plugin took
them over with their rows."""

from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Text, false
from sqlalchemy.orm import Mapped, mapped_column

from hubra.core.extensions import db


class QualificationKind(db.Model):
    """A qualification the club tracks: "J+S Leiter", "Nothelfer", "Laser"."""

    __tablename__ = "qualification_kinds"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(120), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # How long it is valid; None: it does not expire.
    valid_months: Mapped[int | None] = mapped_column(db.Integer, nullable=True)
    # Days before expiry the holder and the managers are reminded.
    remind_days: Mapped[int] = mapped_column(db.Integer, default=30, nullable=False)
    # Members add it to themselves ("Elektriker", "Grafik"), and every member
    # can see who has it. Never what an item takes: nobody checks it.
    self_service: Mapped[bool] = mapped_column(
        db.Boolean, default=False, server_default=false(), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class MemberQualification(db.Model):
    """One member holds one qualification, from a day, maybe until a day.

    One row per member and kind: a renewal moves the dates.
    """

    __tablename__ = "member_qualifications"
    __table_args__ = (
        db.UniqueConstraint("member_id", "kind_id", name="uq_member_qualification"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    member_id: Mapped[int] = mapped_column(
        db.Integer,
        ForeignKey("members.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    kind_id: Mapped[int] = mapped_column(
        db.Integer,
        ForeignKey("qualification_kinds.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    obtained_on: Mapped[date] = mapped_column(db.Date, nullable=False)
    expires_on: Mapped[date | None] = mapped_column(db.Date, nullable=True)
    note: Mapped[str | None] = mapped_column(db.String(500), nullable=True)
    # Set when the reminder went out; cleared by a renewal.
    reminded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_by: Mapped[int | None] = mapped_column(
        db.Integer, ForeignKey("members.id", ondelete="SET NULL"), nullable=True
    )
    # Self-service entries: another member vouches for it ("Bestätigt von").
    # Cleared when the holder changes the note.
    confirmed_by: Mapped[int | None] = mapped_column(
        db.Integer, ForeignKey("members.id", ondelete="SET NULL"), nullable=True
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
