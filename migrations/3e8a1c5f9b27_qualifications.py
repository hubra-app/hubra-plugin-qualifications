"""qualification_kinds, member_qualifications: taken over from Guides

Until Guides 2.0 these were the Guides plugin's tables. Where they exist
(Guides was installed) they are kept as they are, rows and all; otherwise
they are made here, and the Community plugin's "Kann" entries
(``community_skills``, kind ``skill``) become self-service qualifications,
as Guides 1.5 did. Nothing is imported from either plugin.

Roles that could manage qualifications under Guides
(``guides.qualifications.manage``) get the new right
``qualifications.members.manage``.

Safe to run again: tables and rights are only added where missing.

Revision ID: 3e8a1c5f9b27
Revises:
Create Date: 2026-11-09 16:00:00

"""

from datetime import date, datetime, timezone

from alembic import op
import sqlalchemy as sa

from hubra.core.plugins.ops import has_table


revision = "3e8a1c5f9b27"
down_revision = None
branch_labels = None
depends_on = None

OLD_RIGHT = "guides.qualifications.manage"
NEW_RIGHT = "qualifications.members.manage"


def upgrade():
    if not has_table("qualification_kinds"):
        _create_tables()
        _copy_community_skills()
    _carry_the_right()


def _create_tables() -> None:
    op.create_table(
        "qualification_kinds",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("valid_months", sa.Integer(), nullable=True),
        sa.Column("remind_days", sa.Integer(), nullable=False),
        sa.Column(
            "self_service", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "member_qualifications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("member_id", sa.Integer(), nullable=False),
        sa.Column("kind_id", sa.Integer(), nullable=False),
        sa.Column("obtained_on", sa.Date(), nullable=False),
        sa.Column("expires_on", sa.Date(), nullable=True),
        sa.Column("note", sa.String(length=500), nullable=True),
        sa.Column("reminded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("confirmed_by", sa.Integer(), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["member_id"], ["members.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["kind_id"], ["qualification_kinds.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["created_by"], ["members.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["confirmed_by"],
            ["members.id"],
            name="fk_member_qualifications_confirmed_by",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("member_id", "kind_id", name="uq_member_qualification"),
    )
    op.create_index(
        "ix_member_qualifications_member_id", "member_qualifications", ["member_id"]
    )
    op.create_index(
        "ix_member_qualifications_kind_id", "member_qualifications", ["kind_id"]
    )


def _catalog_exists() -> bool:
    """The permission catalog lives in public on Postgres (clubs share it)."""
    bind = op.get_bind()
    schema = "public" if bind.dialect.name == "postgresql" else None
    return sa.inspect(bind).has_table("permissions", schema=schema)


def _carry_the_right() -> None:
    if not has_table("role_permissions") or not _catalog_exists():
        return
    bind = op.get_bind()
    # Hubra lists the right itself on its next permission sync; until then
    # the roles need a row to point at.
    bind.execute(
        sa.text(
            "INSERT INTO permissions"
            " (key, display_name, resource, action, blueprint, is_active)"
            " SELECT :key, 'Manage qualifications', 'members', 'manage',"
            " 'qualifications_bp', :yes WHERE NOT EXISTS"
            " (SELECT 1 FROM permissions WHERE key = :same)"
        ),
        {"key": NEW_RIGHT, "same": NEW_RIGHT, "yes": True},
    )
    bind.execute(
        sa.text(
            "INSERT INTO role_permissions (role_id, permission_id)"
            " SELECT DISTINCT rp.role_id, pn.id FROM role_permissions rp"
            " JOIN permissions po ON po.id = rp.permission_id AND po.key = :old"
            " JOIN permissions pn ON pn.key = :new"
            " WHERE NOT EXISTS (SELECT 1 FROM role_permissions x"
            " WHERE x.role_id = rp.role_id AND x.permission_id = pn.id)"
        ),
        {"old": OLD_RIGHT, "new": NEW_RIGHT},
    )


def _copy_community_skills() -> None:
    if not has_table("community_skills"):
        return
    bind = op.get_bind()
    rows = bind.execute(
        sa.text(
            "SELECT member_id, title, description, created_at FROM community_skills"
            " WHERE kind = 'skill' ORDER BY id"
        )
    ).all()
    if not rows:
        return
    now = datetime.now(timezone.utc)
    kinds = {
        name.strip().casefold(): (kid, self_service)
        for kid, name, self_service in bind.execute(
            sa.text("SELECT id, name, self_service FROM qualification_kinds")
        ).all()
    }
    held = {
        (m, k)
        for m, k in bind.execute(
            sa.text("SELECT member_id, kind_id FROM member_qualifications")
        ).all()
    }
    for member_id, title, description, created_at in rows:
        name = (title or "").strip()[:120]
        if not name:
            continue
        found = kinds.get(name.casefold())
        if found is None:
            bind.execute(
                sa.text(
                    "INSERT INTO qualification_kinds"
                    " (name, remind_days, self_service, created_at)"
                    " VALUES (:name, 30, :yes, :now)"
                ),
                {"name": name, "yes": True, "now": now},
            )
            kid = bind.execute(
                sa.text("SELECT id FROM qualification_kinds WHERE name = :name"),
                {"name": name},
            ).scalar()
            found = kinds[name.casefold()] = (kid, True)
        kid, self_service = found
        # A kind the club manages ("Nothelfer") is not one members may
        # claim for themselves; leave such entries to the managers.
        if not self_service or (member_id, kid) in held:
            continue
        held.add((member_id, kid))
        obtained = _day(created_at)
        bind.execute(
            sa.text(
                "INSERT INTO member_qualifications"
                " (member_id, kind_id, obtained_on, note, created_by, updated_at)"
                " VALUES (:m, :k, :on, :note, :m, :now)"
            ),
            {
                "m": member_id,
                "k": kid,
                "on": obtained or date.today(),
                "note": ((description or "").strip()[:500]) or None,
                "now": now,
            },
        )


def _day(value) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    try:  # SQLite hands back text
        return datetime.fromisoformat(str(value)).date()
    except ValueError:
        return None


def downgrade():
    op.drop_table("member_qualifications")
    op.drop_table("qualification_kinds")
