# chief-of-staff: README

Version 1.7 · desk: MatDuo (Chief of Staff) · used by both agents · owner: Zaim

## Purpose
Make Mahareka's AI staff work as one office: the right staff member takes each piece of work,
answers in its own role, and uses what the office already knows.

## What it does
- Routes work. When Zaim names a staff member ("Hakim, …") or a department ("bagi kat QS"), or
  asks who should handle something, it picks the desk.
- Takes the role. In a Telegram topic that belongs to a desk, the agent answers as that desk's
  staff member for the whole conversation, with the character, limits and skills on its card.
- Asks the machine that holds a skill. Work that only runs on another machine (rates and
  costing run on MatDuo only) is asked through Mission Control and the answer is relayed.
- Searches the desk archives: the notes that match, the notes linked to them, or everything
  every desk knows about one client, project, vendor or trade.
- Lets staff propose a lesson (`LESSON:`, which waits for Zaim's approval) and file an archive
  note (`ARCHIVE:`, a reference that needs no approval).
- The staff are roles, not separate bots. A role changes voice and focus, never authority.

## Why it exists
Without it every request lands on one general assistant, and Zaim has to say who should do
what and repeat what was decided before. With it he writes in a staff member's topic or says a
name, and the role, its skills and its memory come along. One roster, written by Mission
Control, keeps both agents in agreement about who the staff are.

## When it runs
- In every staff topic of the Mahareka HQ group: the topic is bound to this skill, so it loads
  when a new session starts there.
- When Zaim addresses a staff member by name, names a department, or asks who should handle
  something, in any chat.
- It is not scheduled.

## How it works
1. `_tools/roster.py` finds the roster on the machine and prints one staff card.
2. The desk comes from the topic (`Mahareka staff desk: <code>`), from the name Zaim used, or
   from `_shared/routing.md`.
3. The agent answers as that staff member and uses only the skills the card lists as built and
   present on that machine.
4. A skill that lives on the other machine: `_tools/ask_master.py` asks it and prints the answer.
5. Work about a client, a project or an earlier decision: `_tools/archive.py` searches the desk
   archive first.
6. Authority, the Boss desk, lessons and notes follow `_shared/rules.md`.

## Using it (Zaim)
Write in a staff member's topic, or say the name anywhere. After a topic, a skill or the roster
changes, send `/new` in that topic so the new session loads the current version. Decide lessons
on Approvals in Mission Control.

## Maintaining it
- The roster, the desk archives and the hubs are written by Mission Control into the shared
  wiki. Never edit them by hand: change the staff in the Virtual Office.
- Which desk owns which work: `_shared/routing.md`. Rules: `_shared/rules.md`.
- The source is the `mahareka-skills` repo. Tests: `tests/test_chief_of_staff.py`,
  `tests/test_ask_master.py`, `tests/test_archive_search.py` and `icm_check.py`.
- Changing a rule needs Zaim's approval and a version bump. Keep `name:` and the description
  stable so a new version installs over the old one.
- 26 Nov 2026 (v1.7): a staff member keeps its card current inside a long conversation. Every
  card ends with a version; before a new request the staff member asks `roster.py --since`
  and gets the card again only if Zaim approved new memory or a new skill rule. The card's
  skill rules are followed whenever that skill is used.
