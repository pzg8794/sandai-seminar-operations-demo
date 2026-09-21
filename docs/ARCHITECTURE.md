# Architecture

## Objective

Use one versioned codebase and one shared management/testing data plane across local VS Code and Google Colab without allowing silent dataset drift.

```text
PUBLIC / VERSIONED                         SHARED / MANAGEMENT + TESTING

GitHub repository                         RIT Google Shared drive
  code, notebooks, tests                    synthetic input/configuration
  schema contracts                          monitoring state and outputs
  synthetic demonstration data              verification and parity records
           |                                          ^
           | clone                                    | authenticated bridge
           v                                          |
Local VS Code -----------------------------------------+
  explicit refresh into ignored runtime cache
  validation, execution, allowlisted output push
                                                      ^
                                                      | Drive mount
Google Colab ------------------------------------------+
  same notebook logic, same Shared-drive inputs
```

## Responsibility split

### Public GitHub repository

- notebook and library source;
- tests and validation logic;
- schema contracts and configuration examples;
- synthetic seed data;
- strategy and implementation guidance.

It does not contain a Google credential or automatically provide access to the Shared drive. A public clone remains a complete synthetic, reproducible demonstration; the Drive bridge adds the shared VS Code/Colab execution surface.

### RIT Google Shared drive

- management/test configuration;
- synthetic source data used by the shared demo;
- processed weekly metrics;
- channel and partner-pipeline metrics;
- management decision snapshots;
- local and Colab verification records;
- parity results.

The Shared drive is authoritative for shared management/test state. Its folder identifier is a routing value, not an authentication secret; Google Workspace still controls access.

### Local VS Code

- edits the GitHub codebase;
- pulls an explicit runtime cache from the Shared drive;
- validates the marker, schemas, and hashes;
- runs monitoring;
- pushes only derived outputs and verification records.

The local runtime cache is ignored by Git and is disposable. It is not a second data plane and must be refreshed explicitly before operational calculations.

### Google Colab

- mounts the same RIT Shared drive;
- reads the same data/configuration;
- runs the same notebook logic;
- writes only defined derived outputs and its verification record.

The student-facing notebook remains isolated from the management data plane and does not require the Shared drive.

## Data flow

```text
Git commit
  -> notebook/library test
  -> explicit Shared-drive refresh
  -> marker + schema + hash validation
  -> local monitoring run
  -> managed derived-output push
  -> Colab run on same Shared drive
  -> metric parity comparison
```

The local runtime cache is disposable. It is never an independent source of truth, is refreshed explicitly, and is excluded from Git. The bridge must not delete remote data or push source/raw inputs back to the drive.

## Path abstraction

Code resolves an environment-specific project root and then uses paths from the data contract relative to that root:

- local VS Code: ignored runtime cache configured by `workspace-locator.private.json`;
- Google Colab: mounted Shared-drive project root;
- public/synthetic testing: repository-owned synthetic fixtures where a test explicitly selects them.

Machine-specific absolute paths do not belong in committed files. [`workspace-locator.example.json`](../workspace-locator.example.json) documents the local configuration shape without publishing a personal account or credential.

## Promotion model

`SOURCE -> WORKING -> VALIDATED -> SUBMISSION`

An artifact advances only when the required validation evidence exists. A local run does not prove Colab parity, and a produced file does not prove submission.

## Shared data contract

Both execution surfaces must agree on:

- campaign and learner input paths;
- schema and data-classification versions;
- attendance targets and forecasting configuration;
- processed/management output paths;
- source hashes and code revision used for a run;
- verification and parity-result locations.

The system fails closed when required files, schemas, marker fields, or expected hashes do not match. It never interprets a missing source as an empty dataset.

## Methods

- **Business and data understanding:** define the outcome, current process, baseline, stakeholders, and data before automation.
- **CRISP-DM:** business understanding, data understanding, preparation, modeling/analysis, evaluation, and deployment.
- **Iterative SDLC:** deliver one bounded feature, test, deploy, measure, review, and repeat.
- **Layered data architecture:** source evidence becomes structured, validated, contextualized, and decision-supporting information while execution remains measurable and reviewable.
- **Object-oriented design:** reusable validation, configuration, decision, and output responsibilities are kept in explicit components.

## Reliability rules

- no automatic source-data overwrite;
- no automatic deletion of Shared-drive content;
- no passwords, secret keys, tokens, or real personal records in GitHub;
- no silent fallback to a different dataset;
- no claim of parity without matching input/config/code hashes;
- no management-data access from the student-facing notebook;
- no claim that a generated recommendation was executed when the system only calculated it.

## Cross-environment acceptance test

Parity is established only when local VS Code and Colab calculate the same core values from the same input/configuration hashes:

- weekly attendance;
- cumulative attendance;
- show rate;
- required registrations;
- attendance forecast;
- risk status;
- recommended intervention.

Until both verification records exist and the comparison passes, the honest status is **parity unverified**.
