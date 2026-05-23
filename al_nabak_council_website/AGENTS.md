# Project Agent Hierarchy

This project uses a standing review structure for larger changes. Recreate this roster at the start of major feature, QA, or redesign work.

## Hierarchy

1. Product Manager
   - Owns acceptance criteria, scope control, product risks, and release readiness.
   - Confirms what is production-ready and what still needs policy, payment-provider, or operational decisions.

2. Backend Operator 1
   - Owns core domain logic: models, forms, validation, persistence, CSRF, and state transitions.
   - Primary focus areas: projects, donations, voting, tracking, and admin workflows.

3. Backend Operator 2
   - Owns platform behavior: routing, authentication, sessions, language switching, settings, and admin access.
   - Primary focus areas: security regressions, redirects, permissions, and bilingual behavior.

4. Frontend Operator
   - Owns templates, CSS, JavaScript behavior, responsiveness, and UI accessibility implementation.
   - Primary focus areas: layout stability, theme behavior, navigation, forms, and mobile screens.

5. UX/UI Specialist
   - Owns usability, visual identity, beginner friendliness, and Nielsen heuristic review.
   - Primary focus areas: Syrian flag-inspired color usage, clarity, labels, flows, and reducing cognitive load.

6. QA
   - Owns smoke tests, regression checks, bilingual checks, form checks, and release verification.
   - Primary focus areas: public routes, admin routes, auth, donations, project workflows, and Arabic rendering.

## Operating Rules

- The Product Manager defines acceptance criteria before broad changes.
- Backend operators split ownership to avoid overlapping edits.
- Frontend and UX/UI review together, but frontend owns implementation and UX/UI owns critique.
- QA verifies after each meaningful change and reports exact commands, routes, and failures.
- Agents should not overwrite unrelated work.
- Any production payment integration must be treated as a separate security-sensitive project.
