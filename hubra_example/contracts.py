"""What this plugin offers other plugins and the dashboards.

Other plugins never import this package or read ``example_notes``. They use
these contracts through Hubra (docs/contracts.md in hubra-app/hubra):

    from hubra.core.contracts import query
    notes = query("example.notes.latest", limit=3)

and hear of a new note by subscribing to ``example.note.added`` in their
``Module.events``. Schemas are pydantic models; Hubra checks every input and
result against them. Handlers must not commit: Hubra does.
"""

from __future__ import annotations

from pydantic import BaseModel, Field
from sqlalchemy import func, select

from hubra.core.extensions import db

from .models import ExampleNote


class LatestIn(BaseModel):
    limit: int = Field(default=5, ge=1, le=50)


class Note(BaseModel):
    """A note as other plugins see it."""

    id: int
    text: str


class NoteAdded(BaseModel):
    note_id: int


def latest_notes(ctx, data: LatestIn) -> list[Note]:
    """The newest notes first. *ctx* says who asks (ctx.actor, ctx.system)."""
    rows = db.session.scalars(
        select(ExampleNote).order_by(ExampleNote.id.desc()).limit(data.limit)
    ).all()
    return [Note(id=n.id, text=n.text) for n in rows]


def latest_widget(ctx, config: dict) -> dict:
    """The "Latest notes" dashboard widget: a list view
    ({items: [{label, sub?, path?}], total?}). *config* holds the fields the
    member set when adding it."""
    count = max(1, min(int(config.get("count") or 5), 20))
    rows = db.session.scalars(
        select(ExampleNote).order_by(ExampleNote.id.desc()).limit(count)
    ).all()
    total = db.session.scalar(select(func.count()).select_from(ExampleNote))
    items = [
        {
            "label": n.text[:80],
            "sub": f"{n.created_at:%d.%m.%Y}",
            "path": "/app/example",
        }
        for n in rows
    ]
    return {"items": items, "total": total}
