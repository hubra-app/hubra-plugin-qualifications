# Qualifications

[![Test and release](https://github.com/hubra-app/hubra-plugin-qualifications/actions/workflows/release.yml/badge.svg?branch=main)](https://github.com/hubra-app/hubra-plugin-qualifications/actions/workflows/release.yml?query=branch%3Amain) [![License: all rights reserved](https://img.shields.io/badge/license-all%20rights%20reserved-lightgrey)](LICENSE) [![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-bitsandbricks-ffdd00?logo=buymeacoffee&logoColor=black)](https://buymeacoffee.com/bitsandbricks)

A plugin for [Hubra](https://hubra.club). Licences, first aid and machine
inductions: who holds which and until when, with reminders. And *Wer kann
was*: what members can do for the club.

**Version** 1.0.0 · **Works with** Hubra >=0.2.5,<1 · **Plugin id** `qualifications` · **Module** `qualifications`

## What it does

Trainer licences, first aid, machine inductions: *Qualifications* (permission
**Manage qualifications**, `qualifications.members.manage`) lists who holds
which and until when, soonest expiry first, with filters for "expires soon"
and "expired".

- A qualification type has a validity in months (empty: it does not expire)
  and how many days before expiry to remind.
- Entering one again for the same member renews it.
- A daily job notifies the holder and everyone who manages qualifications once
  before it expires; a renewal arms the reminder again.
- Members see their own under *My qualifications* on their account page.
- The [Guides](https://github.com/hubra-app/hubra-plugin-guides) plugin shows
  which qualification a guide (and its item) takes, and whether the reader
  holds it, through the queries `qualifications.kinds.list` and
  `qualifications.member.holds`. Only the club's own kinds are offered there.

## Who can do what

What members can do for the club (electrician, graphic design, first aid
outside the club's own courses) are qualifications too: types switched to
"Members add it themselves". *Wer kann was* (`/app/skills`, every member)
lists who has which, with a search; members add their own there or on their
account page, picking a type or typing a new one, and change or remove only
their own. Managers still see and edit everything under *Qualifications*.
Any other member can confirm an entry ("Bestätigen"); it then shows who
vouched for it, and changing the note clears that. A self-service type can
never be what an item takes, since no manager checked it.

This replaces the "Kann" entries of the Community plugin's skills directory:
installing this plugin copies them here once when the tables are new (when
that table exists; Qualifications does not need Community).

## Moving from Guides

Up to Guides 1.x this was part of the Guides plugin. Install Qualifications
1.0.0 together with Guides 2.0.0:

- it takes over the tables `qualification_kinds` and `member_qualifications`
  with their rows;
- clubs that had Guides on have Qualifications on too (the module lists the
  old code `inventory.guides` under `renamed_from`, which needs the Hubra
  release with hubra-app/hubra#278);
- roles that had **Manage qualifications** (`guides.qualifications.manage`)
  get the new right `qualifications.members.manage`;
- the pages are `/app/qualifications` (the old `/app/inventory/qualifications`
  still opens it) and `/app/skills`; the API is `/api/v1/qualifications`.

## Install

Platform admins install it from the Plugin catalogue in manage
(official Marketplace, <https://plugins.hubra.club/index.json>, signed with
the Hubra project key). Clubs then switch it on under Einstellungen → Module.

## Develop

Clone this repository into `plugins/qualifications` of a Hubra checkout. Its tests
then run with Hubra's (`cd app/backend && pytest ../../plugins/qualifications`), and
`npm run build:plugin` in `app/frontend` builds its frontend. The workflow
does the same against Hubra's `main` on every push and pull request.

## Releasing

Bump `version` in `plugin.yaml`, add a `## <version>` section to
`CHANGELOG.md` and merge. Then tag the merged commit on main and push the tag:

```sh
git switch main && git pull
git tag v<version> && git push origin v<version>
```

The workflow tests the plugin and builds its frontend, the `plugin-signing`
job signs it after your approval, and only then is the GitHub release
`v<version>` published, with `qualifications-<version>.zip` and its `.sha256` attached. Files
listed in `.releaseignore` stay out of the zip. Releases are immutable, so a
published version never changes: fix a bad one with a new version.

Source: <https://github.com/hubra-app/hubra-plugin-qualifications>
