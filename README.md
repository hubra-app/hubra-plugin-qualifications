# Hubra plugin template

Start a new [Hubra](https://hubra.club) plugin from here. The template is a
small plugin that works and uses every part a plugin has: a notice board
with one table, an API, a screen in the club app, a module setting, a
migration, tests, and the workflow that tests, signs and releases it.

**Plugin id** `example` · **Package** `hubra_example` · **Module** `example` · **Works with** Hubra `>=0.2.5,<1`

## Make a new plugin

1. **Create the repository.** Click **Use this template** and name it
   `hubra-plugin-<id>` in `hubra-app`. The Marketplace
   ([hubra-app/hubra-plugins](https://github.com/hubra-app/hubra-plugins))
   lists every public `hubra-plugin-*` repository there once it has a release.
2. **Rename everything called example.** Use the same name in every place:

   | Where | Example | Yours |
   | --- | --- | --- |
   | `plugin.yaml` `id`, `name`, `description`, `homepage`, `tags` | `example` | `<id>` |
   | Package folder and `package:` (must start with `hubra_`) | `hubra_example` | `hubra_<name>` |
   | Module code (`plugin.yaml` `modules:`, `Module(code=...)`, `module:` in `frontend/src/index.tsx`) | `example` | must not clash with a Hubra module |
   | Blueprint name, which sets the permission prefix | `example_bp` gives `example.notes.read` | `<name>_bp` |
   | Table names, in `models.py`, `tables=` and the migration | `example_notes` | prefix them with your id |
   | API path | `/api/v1/app/example` | `/api/v1/app/<id>` (the club area; plugins cannot add platform or global routes) |
   | Club-app route and nav entry | `/app/example` | |
   | Translations (`shell.nav.example`, `example.*`) | | |

   Then replace the migration with your own (`0a1b2c3d4e5f_example_notes.py`)
   and set `version: "1.0.0"` and the first `CHANGELOG.md` entry.

   In `.github/workflows/release.yml`, point the three `uses:` at the
   template instead of the copies, pinned to the newest commit of the
   template's main, and delete `.github/workflows/plugin.yml`,
   `.github/workflows/publish.yml` and `.github/actions/`:

   ```yaml
       uses: hubra-app/hubra-plugins-template/.github/workflows/plugin.yml@<commit> # main
         - uses: hubra-app/hubra-plugins-template/.github/actions/sign@<commit> # main
       uses: hubra-app/hubra-plugins-template/.github/workflows/publish.yml@<commit> # main
   ```

   Keep the `sign` job itself in your `release.yml`: the signing key is an
   environment secret, and only a job of the plugin's own workflow that
   names the environment gets it.

   Every plugin then runs the same checks and signs the same way, and a
   change to them reaches a plugin when you move the pin.
3. **Set up the repository** (Settings):
   - **Rules › Rulesets › Import a ruleset:** import both files from
     [`.github/rulesets/`](.github/rulesets/). `main.json` protects `main`
     (pull request, required check `test`, no force push or delete);
     `tags.json` makes `v*` tags permanent once published.
   - **Environments › New environment** `plugin-signing`: add the secret
     `HUBRA_SIGNING_KEY` (the official plugin key; never a repository or
     organisation secret), add yourself as required reviewer, and limit
     deployment to tags `v*`.
   - Optional repository secret `MARKETPLACE_TOKEN` (Actions: write on
     hubra-app/hubra-plugins), so a release is listed at once instead of
     within the hour.
   - **Code security:** turn on secret scanning, push protection and private
     vulnerability reporting.

## Layout

```
plugin.yaml              # id, version, Hubra range, package, modules, requires, depends
hubra_example/
  __init__.py            # module = Module(...): blueprint, nav entry, setting, tables
  models.py              # SQLAlchemy models (one copy per club schema)
  routes.py              # the API, with permission_required(...)
migrations/              # Alembic revisions of this plugin only
frontend/src/
  index.tsx              # registerPlugin({...}): routes, icons, translations
  NotesScreen.tsx        # the screen
  api.ts                 # calls to the plugin's API
  translations.json      # en-GB and de-CH
tests/test_example.py    # runs with Hubra's pytest fixtures
CHANGELOG.md             # "## <version>" sections, shown before updating
.releaseignore           # kept out of the release zip
.mason.toml              # where Mason finds the version, changelog and tag
.github/workflows/release.yml   # test, sign job, release: calls the template's files
.github/workflows/plugin.yml    # tests (the template's own; plugins use it from here)
.github/actions/sign/           # signs and packs, run by the sign job
.github/workflows/publish.yml   # publishes the GitHub release
.github/rulesets/        # importable rulesets for main and v* tags
```

What a plugin can do (settings, event hooks, Celery tasks, tabs on built-in
screens, slots, connected apps) is in
[plugins/README.md](https://github.com/hubra-app/hubra/blob/main/plugins/README.md)
and [hubra/modules/README.md](https://github.com/hubra-app/hubra/blob/main/app/backend/hubra/modules/README.md).
[hubra-plugin-keys](https://github.com/hubra-app/hubra-plugin-keys) is a
bigger real plugin to compare with.

## Who sees the plugin: `role_defaults`

A role without access to a module doesn't see it at all: not in the
sidebar, on its pages or in its API (`403 MODULE_ACCESS`). Members still see
their own data from it on routes under `/mine` or `/my-…`. `role_defaults`
in `Module(...)` says which standard roles get the module, and at which
level, when a club switches it on for the first time:

```python
role_defaults={"member": "view", "board": "edit", "secretary": "all"},
```

Roles: `member` (Mitglied), `board` (Vorstand), `secretary` (Aktuar/in),
`treasurer` (Kassier/in); admins have everything anyway. Levels: `view`,
`edit`, `all`, as on Einstellungen › Rollen. They are given once and only
added, so what the club changes later stays. Without `role_defaults` only
admins see the module until the club gives a role access. Needs Hubra 0.2.5
or later ([docs/roles.md](https://github.com/hubra-app/hubra/blob/main/docs/roles.md)).

## Talking to other plugins: contracts

A plugin never imports another plugin, reads its tables or calls its REST
routes from the backend. It offers **contracts** instead, and uses others'
through Hubra ([docs/contracts.md](https://github.com/hubra-app/hubra/blob/main/docs/contracts.md)):

- `hubra_example/contracts.py` offers a query (`example.notes.latest`), an
  event (`example.note.added`, sent by `emit()` in `routes.py`) and a
  dashboard widget (`example.latest`, a list). They are listed under
  `provides=` in `hubra_example/__init__.py`.
- To use another plugin's contract, name it under `consumes=` with the
  versions you accept, then `query("inventory.items.get", ids=[3])`,
  `call(...)` or `send(...)` from `hubra.core.contracts`. Subscribe to its
  events under `events=`.
- `plugin.yaml` lists `contracts` under `uses:`.

Widgets show up in the dashboard catalogue for members who may see them
(module on, `perm` held). The handler gets the member's settings for the
widget (`fields=`) and returns a `stat` (`{value, sub?, path?}`) or a `list`
(`{items: [{label, sub?, path?}], total?}`); Hubra draws both. See
[docs/dashboards.md](https://github.com/hubra-app/hubra/blob/main/docs/dashboards.md).

## Add-ons: plugins that build on another plugin

A plugin that uses another plugin's module (a module code like
`inventory.keys`, a slot like `inventory.item`) is an **add-on** of it. Hubra
shows it under that plugin in the Plugin catalogue and on
plugins.hubra.club, and checks the version on every install and update.
Declare both the module and the plugin, with the versions you tested:

```yaml
modules: [inventory.keys]
requires: [inventory]
depends:
  inventory: ">=2.0,<3"
```

The release workflow fails ("The manifest declares every dependency") when
an area the plugin uses is missing from `requires:`, or a plugin it requires
has no version range under `depends:`. The plugin still imports only Hubra
and its own code; it talks to its parent through Hubra's API and slots.

## Develop

Clone the repository into `plugins/<id>` of a Hubra checkout:

```
cd hubra/app/backend
pytest ../../plugins/<id>                       # tests, with Hubra's fixtures
flask plugins revision <id> -m "..." --autogenerate   # with HUBRA_PLUGINS_AUTOINSTALL=<id>
cd ../frontend
npm run typecheck:plugins
npm run build:plugin -- ../../plugins/<id>      # --watch while you work
```

With `HUBRA_PLUGINS_AUTOINSTALL=<id>` a local Hubra loads the plugin from the
checkout without installing it.

## Release

Bump `version` in `plugin.yaml`, add a `## <version>` section to
`CHANGELOG.md` and merge. Then tag the merged commit on main and push the tag:

```sh
git switch main && git pull
git tag v<version> && git push origin v<version>
```

With [Mason](https://github.com/bitsandbricks-ch/mason-cli), `mason bump <repo> minor`
opens the bump PR and `mason release tag <repo>` pushes the tag; `.mason.toml`
tells it to use `plugin.yaml`, `CHANGELOG.md` and `v<version>`.

The workflow tests the plugin and builds its frontend, the `plugin-signing`
job signs it after your approval, and only then is the GitHub release
`v<version>` published, with `<id>-<version>.zip` and its `.sha256` attached. Files
listed in `.releaseignore` stay out of the zip. Releases are immutable, so a
published version never changes: fix a bad one with a new version. The template itself is never signed.

Migrations must keep the previous version working (add columns and tables,
drop them a release later): a rollback in the plugin catalogue does not undo
them.
