# Changelog

## Unreleased

- Kind and entry dialogs use the shared footer (Abbrechen, main action, delete at the left) and save on Enter.

## 1.0.0

Qualifications are their own plugin now; up to Guides 1.x they were part of
Guides. Install together with Guides 2.0.0.

- Takes over `qualification_kinds` and `member_qualifications` with their
  rows; where they don't exist yet they are made, and the Community plugin's
  "Kann" entries are copied in as self-service qualifications.
- Module `qualifications`, on wherever Guides (`inventory.guides`) was on
  (`renamed_from`, needs the Hubra release with hubra-app/hubra#278).
- Right `qualifications.members.manage` (was `guides.qualifications.manage`);
  roles that had the old one get it.
- API under `/api/v1/qualifications` (was `/api/v1/guides/qualifications`).
  Pages `/app/qualifications` and `/app/skills`, the account card
  "My qualifications", and a daily reminder before one expires.
- Query contracts `qualifications.kinds.list` and
  `qualifications.member.holds` for other plugins (Guides).
