# Changelog

## 1.0.1

Security fixes from the plugin audit.

- A qualification members hold can no longer switch between self-service
  and the club's own (409 `KIND_IN_USE`): before, ticking off "self-service"
  turned what members had said about themselves into checked qualifications
  (and back, showing managers' notes in Wer kann was).
- `qualifications.member.holds` asked for a member answers only for that
  member, or for anyone when they manage qualifications. As the system it
  answers as before (Guides asks that way).
- Changing a kind or a member's qualification (dates, note) is in the audit
  log now.
- No qualifications for archived or deleted members; no confirming their
  entries either.
- A self-service kind is removed with its last holder, so adding and
  removing entries can't pile up empty kinds. The club's own kinds stay.
- A JSON body that isn't an object answers 400, not 500. `%` and `_` in the
  Wer kann was search match themselves, not anything.
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
