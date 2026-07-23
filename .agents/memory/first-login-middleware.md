---
name: First-login middleware ordering
description: Constraint for forced password changes and onboarding redirects
---

The first-login middleware must exempt the password-change route for both GET and POST requests. The POST must reach the view and persist the replacement password before the middleware can redirect an incomplete school administrator to setup.

**Why:** Redirecting the POST from middleware prevents the password-change view from running, leaves the temporary password active, and creates a misleading redirect to the setup wizard.

**How to apply:** When changing first-login enforcement, test the complete sequence: temporary login, password-change POST, old-password invalidation, setup redirect, and dashboard access after setup.

The forced password-change form explicitly requires the user to re-enter the temporary password alongside the login identifier before accepting a replacement password. Super Admin school views expose only contact information and the principal responsible, never login credentials or password state details.

**Why:** The temporary credential is a one-time bootstrap secret, while the login identifier remains needed for every later connection; keeping these concerns separate prevents accidental credential disclosure in platform administration screens.

**How to apply:** Keep temporary-password verification server-side and preserve one-time display in the post-school-creation credentials page. Do not add login email/password columns to Super Admin school or user summaries.