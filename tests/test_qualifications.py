"""Qualifications: kinds, members' entries with expiry, renewal, reminders."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from tests.helpers import set_modules
from tests.settings.test_settings_kv import _login, _make_role_and_member

Q = "/api/v1/qualifications"


@pytest.fixture
def club(client, app, db, seeded_db):
    """Kim manages qualifications; Max holds them."""
    set_modules(True, "qualifications")
    app.test_cli_runner().invoke(args=["sync-permissions"])
    tier = seeded_db["tier"]
    kim = _make_role_and_member(
        db, tier, name="Kim", permission_keys=["qualifications.members.manage"]
    )
    max_ = _make_role_and_member(db, tier, name="Max")
    _login(client, "kim@test.ch")
    return {"kim": kim.id, "max": max_.id}


def _kind(client, **body):
    resp = client.post(f"{Q}/kinds", json={"name": "Nothelfer", **body})
    assert resp.status_code == 201, resp.get_json()
    return resp.get_json()


def test_add_with_default_expiry_and_renew(client, db, club):
    from hubra_qualifications.routes import add_months

    kind = _kind(client, validMonths=24, remindDays=60)
    got = date.today() - timedelta(days=10)
    resp = client.post(
        Q,
        json={
            "memberId": club["max"],
            "kindId": kind["id"],
            "obtainedOn": got.isoformat(),
        },
    )
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["expiresOn"] == add_months(got, 24).isoformat()
    assert body["state"] == "valid" and body["memberName"] == "Test Max"

    # The same member and kind again: a renewal of the one entry.
    again = client.post(
        Q,
        json={
            "memberId": club["max"],
            "kindId": kind["id"],
            "obtainedOn": date.today().isoformat(),
        },
    )
    assert again.status_code == 200
    assert len(client.get(Q).get_json()) == 1


def test_add_months_keeps_the_end_of_month():
    from hubra_qualifications.routes import add_months

    assert add_months(date(2026, 1, 31), 1) == date(2026, 2, 28)
    assert add_months(date(2024, 2, 29), 12) == date(2025, 2, 28)
    assert add_months(date(2026, 11, 5), 14) == date(2028, 1, 5)


def test_states_and_filter(client, db, club):
    kind = _kind(client, remindDays=30)
    today = date.today()
    _make = lambda member, exp: client.post(  # noqa: E731
        Q,
        json={
            "memberId": member,
            "kindId": kind["id"],
            "obtainedOn": (today - timedelta(days=400)).isoformat(),
            "expiresOn": exp.isoformat(),
        },
    )
    assert (
        _make(club["max"], today - timedelta(days=1)).get_json()["state"] == "expired"
    )
    assert _make(club["kim"], today + timedelta(days=10)).get_json()["state"] == "soon"
    assert [r["memberId"] for r in client.get(f"{Q}?state=expired").get_json()] == [
        club["max"]
    ]
    assert [r["memberId"] for r in client.get(f"{Q}?state=soon").get_json()] == [
        club["kim"]
    ]


def test_never_expiring(client, db, club):
    kind = _kind(client)
    body = client.post(
        Q,
        json={
            "memberId": club["max"],
            "kindId": kind["id"],
            "obtainedOn": "2020-03-01",
        },
    ).get_json()
    assert body["expiresOn"] is None and body["state"] == "valid"


def test_reminder_once_and_again_after_renewal(client, db, club):
    from hubra.core.models.notification import Notification
    from hubra_qualifications.routes import remind

    kind = _kind(client, validMonths=12, remindDays=30)
    today = date.today()
    q = client.post(
        Q,
        json={
            "memberId": club["max"],
            "kindId": kind["id"],
            "obtainedOn": (today - timedelta(days=350)).isoformat(),
        },
    ).get_json()
    assert q["state"] == "soon"
    assert remind() == 1
    db.session.commit()
    to_max = db.session.query(Notification).filter_by(member_id=club["max"]).all()
    to_kim = db.session.query(Notification).filter_by(member_id=club["kim"]).all()
    assert len(to_max) == 1 and "Nothelfer" in to_max[0].title
    assert len(to_kim) == 1 and "Test Max" in to_kim[0].title
    assert remind() == 0  # once

    client.patch(f"{Q}/{q['id']}", json={"obtainedOn": today.isoformat()})
    assert remind() == 0  # renewed: a year away
    assert remind(today + timedelta(days=340)) == 1


def test_mine_and_permissions(client, db, club):
    kind = _kind(client)
    client.post(
        Q,
        json={
            "memberId": club["max"],
            "kindId": kind["id"],
            "obtainedOn": "2025-01-01",
        },
    )
    _login(client, "max@test.ch")
    mine = client.get(f"{Q}/mine").get_json()
    assert [m["kindName"] for m in mine] == ["Nothelfer"]
    assert client.get(f"{Q}/kinds").status_code == 200
    assert client.get(Q).status_code == 403
    assert client.post(f"{Q}/kinds", json={"name": "x"}).status_code == 403
    assert (
        client.post(Q, json={"memberId": club["max"], "kindId": kind["id"]}).status_code
        == 403
    )


def test_validation(client, db, club):
    kind = _kind(client)
    assert client.post(f"{Q}/kinds", json={"name": "Nothelfer"}).status_code == 409
    for body in (
        {},
        {"name": ""},
        {"name": "x", "validMonths": 0},
        {"name": "x", "remindDays": -1},
    ):
        assert client.post(f"{Q}/kinds", json=body).status_code == 400, body
    base = {"memberId": club["max"], "kindId": kind["id"]}
    for extra in (
        {},
        {"obtainedOn": "gestern"},
        {"obtainedOn": (date.today() + timedelta(days=1)).isoformat()},
        {"obtainedOn": "2025-01-01", "expiresOn": "2024-01-01"},
        {"obtainedOn": "2025-01-01", "note": ["x"]},
    ):
        assert client.post(Q, json={**base, **extra}).status_code == 400, extra
    assert (
        client.post(
            Q, json={"memberId": 999, "kindId": kind["id"], "obtainedOn": "2025-01-01"}
        ).status_code
        == 400
    )


def test_members_add_what_they_can_do(client, db, club):
    managed = _kind(client)  # Nothelfer: the club confirms it
    _login(client, "max@test.ch")
    added = client.post(f"{Q}/mine", json={"name": " Elektriker ", "note": "EFZ"})
    assert added.status_code == 201, added.get_json()
    body = added.get_json()
    assert body["kindName"] == "Elektriker" and body["selfService"] is True
    assert body["note"] == "EFZ" and body["expiresOn"] is None
    # The same name again, in other case: the one kind, and only once.
    assert client.post(f"{Q}/mine", json={"name": "elektriker"}).status_code == 409
    # Managed kinds are not for members to claim.
    assert client.post(f"{Q}/mine", json={"kindId": managed["id"]}).status_code == 403
    assert client.post(f"{Q}/mine", json={"name": "nothelfer"}).status_code == 403
    assert client.post(f"{Q}/mine", json={"kindId": 999}).status_code == 404
    assert client.post(f"{Q}/mine", json={}).status_code == 400

    # Kim finds Max by the kind or the note, and adds the same kind by id.
    _login(client, "kim@test.ch")
    kinds = {k["name"]: k for k in client.get(f"{Q}/kinds").get_json()}
    assert kinds["Elektriker"]["selfService"] is True
    assert kinds["Nothelfer"]["selfService"] is False
    assert (
        client.post(f"{Q}/mine", json={"kindId": kinds["Elektriker"]["id"]}).status_code
        == 201
    )
    found = client.get(f"{Q}/directory?q=efz").get_json()
    assert [(r["memberName"], r["kindName"], r["mine"]) for r in found] == [
        ("Test Max", "Elektriker", False)
    ]
    assert len(client.get(f"{Q}/directory?q=elektr").get_json()) == 2
    # Managed qualifications never show in the directory.
    client.post(
        Q,
        json={
            "memberId": club["max"],
            "kindId": managed["id"],
            "obtainedOn": "2025-01-01",
        },
    )
    assert client.get(f"{Q}/directory?q=nothelfer").get_json() == []

    # Max edits and removes only his own self-service entries.
    _login(client, "max@test.ch")
    mine = {m["kindName"]: m for m in client.get(f"{Q}/mine").get_json()}
    assert set(mine) == {"Elektriker", "Nothelfer"}
    assert (
        client.patch(
            f"{Q}/mine/{mine['Elektriker']['id']}", json={"note": "Starkstrom"}
        ).get_json()["note"]
        == "Starkstrom"
    )
    assert client.delete(f"{Q}/mine/{mine['Nothelfer']['id']}").status_code == 403
    kims = [r for r in client.get(f"{Q}/directory").get_json() if not r["mine"]]
    assert client.delete(f"{Q}/mine/{kims[0]['id']}").status_code == 404
    assert client.delete(f"{Q}/mine/{mine['Elektriker']['id']}").status_code == 204
    assert [m["kindName"] for m in client.get(f"{Q}/mine").get_json()] == ["Nothelfer"]


def test_another_member_confirms_a_self_service_entry(client, db, club):
    from hubra.core.models.notification import Notification

    managed = _kind(client)
    _login(client, "max@test.ch")
    entry = client.post(f"{Q}/mine", json={"name": "Elektriker", "note": "EFZ"})
    entry = entry.get_json()
    assert entry["confirmedBy"] is None
    # Not one's own.
    assert client.post(f"{Q}/{entry['id']}/confirm").status_code == 403

    _login(client, "kim@test.ch")
    got = client.post(f"{Q}/{entry['id']}/confirm")
    assert got.status_code == 200, got.get_json()
    assert got.get_json()["confirmedBy"] == "Test Kim"
    assert client.post(f"{Q}/{entry['id']}/confirm").status_code == 200  # again: same
    row = client.get(f"{Q}/directory?q=elektr").get_json()[0]
    assert row["confirmedBy"] == "Test Kim" and row["confirmedById"] == club["kim"]
    notes = db.session.query(Notification).filter_by(member_id=club["max"]).all()
    assert any("confirmed" in n.title for n in notes)
    # Managed qualifications are not confirmed this way.
    held = client.post(
        Q,
        json={
            "memberId": club["max"],
            "kindId": managed["id"],
            "obtainedOn": "2025-01-01",
        },
    ).get_json()
    assert client.post(f"{Q}/{held['id']}/confirm").status_code == 404

    # A new claim needs a new confirmation.
    _login(client, "max@test.ch")
    assert (
        client.patch(f"{Q}/mine/{entry['id']}", json={"note": "EFZ"}).get_json()[
            "confirmedBy"
        ]
        == "Test Kim"
    )
    assert (
        client.patch(f"{Q}/mine/{entry['id']}", json={"note": "Meister"}).get_json()[
            "confirmedBy"
        ]
        is None
    )
    # Only the confirmer (or a manager) takes it back.
    _login(client, "kim@test.ch")
    client.post(f"{Q}/{entry['id']}/confirm")
    _login(client, "max@test.ch")
    assert client.delete(f"{Q}/{entry['id']}/confirm").status_code == 403
    _login(client, "kim@test.ch")
    assert client.delete(f"{Q}/{entry['id']}/confirm").get_json()["confirmedBy"] is None


def test_queries_offer_the_clubs_own_kinds_and_who_holds_them(client, db, club):
    """What Inventory asks (contracts.py): never the self-service kinds."""
    from hubra.core.contracts import SYSTEM, query

    first_aid = _kind(client)
    laser = _kind(client, name="Laser", validMonths=12)
    grafik = _kind(client, name="Grafik", selfService=True)
    resp = client.post(
        Q,
        json={
            "memberId": club["max"],
            "kindId": laser["id"],
            "obtainedOn": "2025-01-01",
        },
    )
    assert resp.status_code == 201, resp.get_json()

    kinds = query("qualifications.kinds.list", actor=SYSTEM)
    assert [k["name"] for k in kinds] == ["Laser", "Nothelfer"]
    assert query(
        "qualifications.kinds.list", ids=[laser["id"], grafik["id"]], actor=SYSTEM
    ) == [{"id": laser["id"], "name": "Laser", "valid_months": 12}]

    held = query(
        "qualifications.member.holds",
        member_id=club["max"],
        kind_ids=[laser["id"], first_aid["id"], grafik["id"], 999],
        actor=SYSTEM,
    )
    assert [(h["kind_id"], h["state"]) for h in held] == [
        (laser["id"], "expired"),
        (first_aid["id"], None),
    ]


def test_holds_for_a_member_only_their_own(client, db, club):
    """Asked for a member, holds answers for that member, or anyone for a manager."""
    from hubra.core.contracts import ActionForbidden, query
    from hubra.core.models.member import Member

    laser = _kind(client, name="Laser")
    kim, max_ = db.session.get(Member, club["kim"]), db.session.get(Member, club["max"])
    ask = dict(kind_ids=[laser["id"]])
    assert query("qualifications.member.holds", member_id=max_.id, actor=max_, **ask)
    assert query("qualifications.member.holds", member_id=max_.id, actor=kim, **ask)
    with pytest.raises(ActionForbidden):
        query("qualifications.member.holds", member_id=kim.id, actor=max_, **ask)


def test_kind_with_holders_keeps_self_service(client, db, club):
    """A self-claimed entry never turns into a club-checked one (and back)."""
    _login(client, "max@test.ch")
    added = client.post(f"{Q}/mine", json={"name": "Laser-Einführung"}).get_json()
    _login(client, "kim@test.ch")
    kid = added["kindId"]
    resp = client.patch(f"{Q}/kinds/{kid}", json={"selfService": False})
    assert resp.status_code == 409
    assert client.get(f"{Q}/kinds").get_json()[0]["selfService"] is True
    # Renaming is fine; so is switching once nobody holds it.
    assert client.patch(f"{Q}/kinds/{kid}", json={"name": "Laser"}).status_code == 200
    # A self-service kind nobody holds can switch.
    empty = _kind(client, name="Grafik", selfService=True)
    resp = client.patch(f"{Q}/kinds/{empty['id']}", json={"selfService": False})
    assert resp.status_code == 200 and resp.get_json()["selfService"] is False


def test_unused_self_service_kinds_go(client, db, club):
    """Adding and removing entries leaves no empty self-service kinds."""
    managed = _kind(client)
    _login(client, "max@test.ch")
    for i in range(3):
        added = client.post(f"{Q}/mine", json={"name": f"Spam {i}"}).get_json()
        assert client.delete(f"{Q}/mine/{added['id']}").status_code == 204
    shared = client.post(f"{Q}/mine", json={"name": "Grafik"}).get_json()
    _login(client, "kim@test.ch")
    kims = client.post(f"{Q}/mine", json={"kindId": shared["kindId"]}).get_json()
    names = [k["name"] for k in client.get(f"{Q}/kinds").get_json()]
    assert names == ["Grafik", "Nothelfer"]
    # Someone else still holds it: it stays; the last one takes it along,
    # also when a manager removes the entry.
    assert client.delete(f"{Q}/mine/{kims['id']}").status_code == 204
    assert len(client.get(f"{Q}/kinds").get_json()) == 2
    assert client.delete(f"{Q}/{shared['id']}").status_code == 204
    assert [k["id"] for k in client.get(f"{Q}/kinds").get_json()] == [managed["id"]]
    # The club's own kinds stay without holders.
    q = client.post(
        Q,
        json={
            "memberId": club["max"],
            "kindId": managed["id"],
            "obtainedOn": "2026-01-01",
        },
    ).get_json()
    assert client.delete(f"{Q}/{q['id']}").status_code == 204
    assert len(client.get(f"{Q}/kinds").get_json()) == 1


def test_bad_bodies_and_wildcards(client, db, club):
    kind = _kind(client)
    assert client.post(f"{Q}/kinds", json=["x"]).status_code == 400
    assert client.post(Q, json=[1]).status_code == 400
    assert client.patch(f"{Q}/kinds/{kind['id']}", json=5).status_code in (200, 400)
    _login(client, "max@test.ch")
    assert client.post(f"{Q}/mine", json=["x"]).status_code == 400
    client.post(f"{Q}/mine", json={"name": "Grafik"})
    # % and _ are searched for as such, not as wildcards.
    assert client.get(f"{Q}/directory?q=%25").get_json() == []
    assert client.get(f"{Q}/directory?q=_").get_json() == []
    assert len(client.get(f"{Q}/directory?q=graf").get_json()) == 1


def test_changes_are_audited(client, db, club):
    from hubra.core.models.audit import AuditEntry
    from sqlalchemy import select

    kind = _kind(client, validMonths=12)
    client.patch(f"{Q}/kinds/{kind['id']}", json={"remindDays": 10})
    q = client.post(
        Q,
        json={
            "memberId": club["max"],
            "kindId": kind["id"],
            "obtainedOn": "2026-01-01",
        },
    ).get_json()
    client.patch(f"{Q}/{q['id']}", json={"expiresOn": "2099-01-01"})
    actions = set(db.session.scalars(select(AuditEntry.action)))
    assert {
        "qualifications.kind.update",
        "qualifications.qualification.update",
    } <= actions
