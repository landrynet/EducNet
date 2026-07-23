---
name: Timetable stabilization rules
description: Durable rules for timetable status, course assignments, conflicts, and permissions
---

Timetable mutations must be server-validated and transactional: only secretaries can manage entries or statuses, course slots exclude pauses, subjects must belong to the classroom, and teachers must be active staff assigned to that subject in the same school.

**Why:** The timetable UI uses AJAX and dynamic teacher loading, so client-side state can become stale or be tampered with; database-backed validation is required to prevent false success messages, cross-school assignments, and intermittent conflict races.

**How to apply:** Keep status changes explicit among `draft`, `preparing`, and `published`; do not auto-advance status when adding a course. Preserve timeslots when deleting entries and keep teacher lists scoped to the selected classroom subject.