# Public browser experience

Public review: https://sandai-seminar-demo-qkpntto5ya-uc.a.run.app/

## Architecture

The public experience uses a React/Vite frontend with a stateless Python service. Existing SaNDAI domain objects remain authoritative: the browser renders an exported public sample from the same campaign logic, while the student-plan endpoint uses the existing learning-plan object.

No real participant database, autonomous outreach, payments, live AI agent, or private operational dataset is connected to the public demonstration.

## Verification summary

- Python regression tests and JavaScript presentation-model tests passed during the final website pass.
- The production frontend build passed.
- Desktop management and mobile student views were visually inspected.
- Week 3 exposes the missed weekly target instead of hiding it inside the cumulative total.
- Week 4 shows a modeled recovery comparison.
- The student workshop preserves progress across its five steps during the browser session and can generate a downloadable takeaway.
- Public root, week selection, mobile layout, and the student-plan endpoint were checked after deployment.
- The website uses illustrative data and clearly distinguishes modeled results from live outcomes.

## Public-review boundary

The website and repository are presentation and reproducibility surfaces for a hypothetical case. They intentionally exclude internal correspondence, working drafts, private workspace maps, access-control notes, and machine-specific deployment configuration.

The strategy explains the plan; the website demonstrates decisions and learner value; the notebooks and source provide optional technical evidence.
