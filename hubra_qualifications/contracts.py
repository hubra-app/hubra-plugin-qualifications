"""What Qualifications offers other plugins (Hubra docs/contracts.md).

Guides names the qualification a guide (and its item) takes and shows whether a member
holds it through these queries, without importing this package or reading
its tables. Only the club's own qualifications (not the self-service ones
members add to themselves) are offered: nobody checked those.
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field
from sqlalchemy import select

from hubra.core.extensions import db

from .models import QualificationKind

MAX_KINDS = 500


class KindsIn(BaseModel):
    """Empty: every kind. With ``ids``: those kinds that still exist."""

    ids: list[int] | None = Field(default=None, max_length=MAX_KINDS)


class Kind(BaseModel):
    id: int
    name: str
    valid_months: int | None = None


class HoldsIn(BaseModel):
    member_id: int
    kind_ids: list[int] = Field(max_length=MAX_KINDS)


class Held(BaseModel):
    """``state``: valid, soon (expires within the reminder days) or expired;
    ``None`` when the member doesn't hold it."""

    kind_id: int
    state: str | None = None
    expires_on: date | None = None


def _managed():
    return select(QualificationKind).where(QualificationKind.self_service.is_(False))


def list_kinds(ctx, data: KindsIn) -> list[Kind]:
    """The club's own qualification kinds, by name."""
    query = _managed()
    if data.ids is not None:
        query = query.where(QualificationKind.id.in_(data.ids))
    rows = db.session.scalars(query.order_by(QualificationKind.name)).all()
    return [Kind(id=k.id, name=k.name, valid_months=k.valid_months) for k in rows]


def member_holds(ctx, data: HoldsIn) -> list[Held]:
    """Whether the member holds each of these kinds (self-service ones are
    left out, unknown ones too)."""
    from .models import MemberQualification
    from .routes import state

    ids = list(dict.fromkeys(data.kind_ids))
    kinds = {
        k.id: k
        for k in db.session.scalars(
            _managed().where(QualificationKind.id.in_(ids))
        ).all()
    }
    held = {
        q.kind_id: q
        for q in db.session.scalars(
            select(MemberQualification)
            .where(MemberQualification.member_id == data.member_id)
            .where(MemberQualification.kind_id.in_(list(kinds)))
        ).all()
    }
    today = date.today()
    out = []
    for kid in ids:
        kind = kinds.get(kid)
        if kind is None:
            continue
        q = held.get(kid)
        out.append(
            Held(
                kind_id=kid,
                state=state(q, kind, today) if q else None,
                expires_on=q.expires_on if q else None,
            )
        )
    return out
