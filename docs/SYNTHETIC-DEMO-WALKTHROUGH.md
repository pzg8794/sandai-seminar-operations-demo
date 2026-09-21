# SaNDAI Participant Demo Walkthrough

> Every student, behavior, score, and result on this page is fictional. This is a product demonstration for the SaNDAI assignment.

## What the prototype proves

The solution connects the full operating loop:

**seminar attendance → learning engagement → explainable risk → next-best action → program improvement**

The management notebook reads 32 sample participant profiles. Each profile has a clear demo name, a `SYN-*` identifier, a career goal, preferred learning format, seminar-attendance status, companion progress, feedback, and recent activity. The OOP `StudentSupportEngine` converts those observable signals into a transparent engagement score, GREEN/YELLOW/RED status, and recommended action.

## Four example participant journeys

### 1. Demo Student Avery Example — ready to advance

- **Profile:** undergraduate beginner exploring a data-analyst role; prefers a worked example.
- **Observed:** attended the seminar, completed 3/3 checkpoints, submitted 5/5 feedback, and was active today.
- **Result:** engagement **100**, status **GREEN**.
- **Recommendation:** invite Avery to the next practice activity and offer an optional peer-referral path.
- **Why it matters:** strong participants receive a useful next step instead of disappearing after one seminar.

### 2. Demo Student Quinn Fiction — one reminder can recover momentum

- **Profile:** career changer exploring data engineering; prefers short video plus practice.
- **Observed:** attended, completed 2/3 checkpoints, and explicitly requested a reminder.
- **Result:** engagement **73**, status **YELLOW**.
- **Recommendation:** send one checkpoint reminder tied to Quinn's stated career goal.
- **Why it matters:** the intervention is small, specific, and connected to the student's reason for attending.

### 3. Demo Student Riley Prototype — navigation is the blocker

- **Profile:** career changer exploring software engineering; prefers short video plus practice.
- **Observed:** attended, completed 1/3 checkpoints, rated the experience 2/5, requested navigation help, and has been inactive for five days.
- **Result:** engagement **51**, status **RED**.
- **Recommendation:** share the notebook navigation guide and the quickest route through the seminar companion.
- **Why it matters:** the system does not guess that Riley lacks ability; it responds to the visible navigation and progress signals.

### 4. Demo Student Casey Demo — recover a missed seminar

- **Profile:** undergraduate exploring education with AI; prefers a visual walkthrough.
- **Observed:** did not attend, has not started the companion, and has been inactive for seven days.
- **Result:** engagement **0**, status **RED**.
- **Recommendation:** invite Casey to the next seminar and share the five-minute catch-up path.
- **Why it matters:** a missed session becomes a recoverable path rather than a lost student.

## How student evidence improves the program

The prototype also aggregates the sample profiles by preferred learning format:

| Sample signal | What management learns | Small next test |
|---|---|---|
| Visual-walkthrough group has the lowest engagement and all eight profiles need support | The notebook may be hard to navigate visually | Add a one-page visual map with the quickest route highlighted |
| Short-video-plus-practice group also shows broad support need | Students may need a smaller entry point before the full activity | Test a five-minute recap followed by one hands-on task |
| Checklist group has high engagement with only two support cases | Explicit sequencing appears useful | Publish a Start → Practice → Finish checklist for everyone |
| Worked-example group completes consistently | A complete model helps students begin | Put one worked example before independent practice |

These are not claims about real students. They demonstrate how the future program could use observed results to choose a small improvement, deploy it, measure the change, and keep or revise it.

## Student-facing result

The separate Student Seminar Companion shows what SaNDAI is offering, not only what management tracks. Its default example profile, **Demo Student Avery Example**, moves through:

1. a short career-readiness reflection;
2. one structured AI prompt exercise;
3. an evidence inventory;
4. a truthful résumé-bullet draft;
5. a time-boxed plan for the next week;
6. a before → after outcome card.

That makes the value proposition concrete: a student leaves with **one explainable artifact and one realistic next action**, while management receives enough aggregate evidence to improve the next seminar.

## Run the example

1. Open `Piter_Garcia_SaNDAI_Management_Command_Center.ipynb` to see campaign performance, profiles, risk, interventions, and program tests.
2. Open `Piter_Garcia_SaNDAI_Student_Seminar_Companion.ipynb` to experience the student path.
3. Run `python -m pytest -q tests/test_data_plane.py` to verify the OOP logic.
4. Run `python scripts/test_artifacts.py --all` to execute both notebooks top to bottom.
