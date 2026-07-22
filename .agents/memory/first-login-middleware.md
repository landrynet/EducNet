---
name: First-login middleware ordering
description: Constraint for forced password changes and onboarding redirects
---

The first-login middleware must exempt the password-change route for both GET and POST requests. The POST must reach the view and persist the replacement password before the middleware can redirect an incomplete school administrator to setup.

**Why:** Redirecting the POST from middleware prevents the password-change view from running, leaves the temporary password active, and creates a misleading redirect to the setup wizard.

**How to apply:** When changing first-login enforcement, test the complete sequence: temporary login, password-change POST, old-password invalidation, setup redirect, and dashboard access after setup.