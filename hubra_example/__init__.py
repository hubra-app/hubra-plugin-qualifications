"""Example: a notice board, the smallest plugin that uses every part.

Rename it before you build on it (see TEMPLATE.md): the plugin id, the
package name (hubra_<something>), the module code, the table and the
permission resource.
"""

from hubra.core.contracts import (
    WidgetField,
    event_contract,
    query_contract,
    widget_contract,
)
from hubra.core.modules import Blueprint, Module, NavItem, SettingField

module = Module(
    code="example",
    name="Example",
    description="A notice board: short notes for the whole club",
    default_enabled=False,
    # Which standard roles get the module, and at which level, when a club
    # switches it on for the first time (docs/roles.md in hubra-app/hubra).
    # Without it only admins see the module until the club gives a role
    # access on Einstellungen › Rollen.
    role_defaults={"member": "view", "board": "edit", "secretary": "all"},
    depends_on=("members",),
    blueprints=(
        Blueprint(
            "hubra_example.routes",
            "example_bp",
            "/api/v1/app/example",
        ),
    ),
    nav=(
        NavItem(
            "/app/example",
            "shell.nav.example",
            "note",
            section="more",
            order=90,
            perms=("example.notes.read",),
        ),
    ),
    settings=(
        SettingField(
            "max_notes",
            "int",
            default=50,
            label="Most notes on the board",
            description="Older notes are hidden once there are more",
        ),
    ),
    # Every table the plugin owns: new clubs get them, and autogenerate only
    # looks at these.
    tables=("example_notes",),
    # What other plugins and the dashboards may use (docs/contracts.md).
    # Names start with the module code; the version is a whole number that
    # goes up when a field is removed or changes meaning.
    provides=(
        query_contract(
            "example.notes.latest",
            "hubra_example.contracts:latest_notes",
            input="hubra_example.contracts:LatestIn",
            output="hubra_example.contracts:Note",
            perm="example.notes.read",
            description="The newest notes",
        ),
        event_contract(
            "example.note.added",
            "hubra_example.contracts:NoteAdded",
            description="A note was added",
        ),
        widget_contract(
            "example.latest",
            "hubra_example.contracts:latest_widget",
            # Translation keys (frontend/src/translations.json) or plain text.
            label="example.widget.latest",
            description="example.widget.latestHint",
            size="m",
            view="list",
            fields=(
                WidgetField("count", "example.widget.count", kind="number", default=5),
            ),
            perm="example.notes.read",
        ),
    ),
    # To use another plugin's contracts, name them with the versions you
    # accept; anything not listed is refused. E.g.
    # consumes={"inventory.items.get": ">=1,<2"},
)
