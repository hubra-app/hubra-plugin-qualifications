"""Qualifications: licences, first aid, inductions with their expiry and
reminders, and who can do what for the club.

Until Guides 2.0 this was part of the Guides plugin (module
``inventory.guides``). This plugin took over its tables and rows; the module
lists that code under ``renamed_from``, so clubs that had Guides on have
Qualifications on too, and its migration gives the roles that could manage
qualifications (``guides.qualifications.manage``) the new right.
"""

from hubra.core.contracts import query_contract
from hubra.core.modules import Blueprint, Module, NavItem, Schedule

_C = "hubra_qualifications.contracts"

module = Module(
    code="qualifications",
    renamed_from=("inventory.guides",),
    # Access the standard roles get when a club first switches it on
    # (docs/roles.md in hubra-app/hubra).
    role_defaults={"member": "view", "board": "edit"},
    name="Qualifications",
    description=(
        "Licences, first aid and inductions with expiry and reminders, "
        "and who can do what"
    ),
    default_enabled=False,
    depends_on=("members",),
    blueprints=(
        Blueprint(
            "hubra_qualifications.routes",
            "qualifications_bp",
            "/api/v1/qualifications",
        ),
    ),
    nav=(
        # Who can do what: every member, next to the other member pages.
        NavItem(
            "/app/skills",
            "shell.nav.canDo",
            "tools",
            section="more",
            order=30,
        ),
        NavItem(
            "/app/qualifications",
            "shell.nav.qualifications",
            "certificate",
            order=34,
            perms=("qualifications.members.manage",),
        ),
    ),
    tasks=("hubra_qualifications.tasks",),
    schedule=(
        Schedule(
            "qualifications-remind",
            "hubra_qualifications.tasks.remind",
            86400.0,
        ),
    ),
    tables=("qualification_kinds", "member_qualifications"),
    # What other plugins may ask (Hubra docs/contracts.md); Guides shows the
    # qualification a guide takes, and whether the reader holds it.
    provides=(
        query_contract(
            "qualifications.kinds.list",
            f"{_C}:list_kinds",
            input=f"{_C}:KindsIn",
            output=f"{_C}:Kind",
            description="The club's own qualification kinds (not self-service ones)",
        ),
        query_contract(
            "qualifications.member.holds",
            f"{_C}:member_holds",
            input=f"{_C}:HoldsIn",
            output=f"{_C}:Held",
            description="Whether a member holds these qualifications, and until when",
        ),
    ),
)
