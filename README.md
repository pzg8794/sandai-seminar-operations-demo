# SaNDAI Seminar Growth & Learning Studio

Public case-challenge prototype by **Piter Garcia**.

This repository contains the reviewer-facing strategy, interactive website source, executable notebooks, synthetic demonstration data, and reproducible calculation logic for an eight-week student-seminar growth plan.

## Start here

1. **Interactive website:** https://sandai-seminar-demo-qkpntto5ya-uc.a.run.app/
2. **Three-minute review guide:** [START-HERE.md](START-HERE.md)
3. **Eight-week strategy PDF:** [strategy/Piter_Garcia_SaNDAI_8_Week_Seminar_Growth_Plan.pdf](strategy/Piter_Garcia_SaNDAI_8_Week_Seminar_Growth_Plan.pdf)
4. **Management notebook:** [notebooks/Piter_Garcia_SaNDAI_Management_Command_Center.ipynb](notebooks/Piter_Garcia_SaNDAI_Management_Command_Center.ipynb)
5. **Student AI Career Lab:** [notebooks/Piter_Garcia_SaNDAI_Student_Seminar_Companion.ipynb](notebooks/Piter_Garcia_SaNDAI_Student_Seminar_Companion.ipynb)
6. **Requirement traceability:** [docs/REQUIREMENT_TRACEABILITY.md](docs/REQUIREMENT_TRACEABILITY.md)

## What the prototype demonstrates

- a weekly attendance operating model with a 20-person floor;
- cumulative progress toward 160+ attendances;
- early-warning forecasting and a recovery scenario;
- channel and partner contribution;
- a free-seminar-to-follow-up value funnel;
- a guided, student-facing AI career activity;
- explicit ownership, collaborative execution, and recurring decision gates.

## Public demonstration boundary

All campaign and learner records in this repository are **synthetic demonstration data**. The project does not claim live recruitment, institutional endorsement, revenue, student tracking, autonomous outreach, or a production AI agent.

Private workspace configuration, internal correspondence, reviewer notes, working drafts, and operational identifiers are intentionally excluded from the reviewer-facing repository.

## Repository map

| Area | Purpose |
| --- | --- |
| `web/` | Public React interface and stateless Python endpoint |
| `notebooks/` | Management and student-facing executable demonstrations |
| `src/` | Reusable metrics, forecasting, validation, and learning logic |
| `config/` | Public synthetic-demo configuration and schemas |
| `data/synthetic/` | Synthetic campaign and learner inputs |
| `tests/` | Reproducibility and regression tests |
| `strategy/` | Final strategy DOCX/PDF |
| `docs/` | Reviewer-facing guides, architecture, and traceability |

## Reproducibility

The website uses the same public sample calculations as the Python domain objects. The notebooks default to the public sample path so an external reviewer does not need access to any private workspace.

See [docs/WEB-EXPERIENCE.md](docs/WEB-EXPERIENCE.md) for the public web verification summary and [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for implementation details.
