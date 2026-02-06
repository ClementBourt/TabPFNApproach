# Goal: Dependency Setup

**Session Period:** 2026-02-06 16:00 to 2026-02-06 16:20

## Objective

Add TabPFN and related dependencies to the project, enabling the forecasting pipeline to use the tabpfn-time-series package.

## Motivation

The TabPFN forecasting approach requires several dependencies: tabpfn, gluonts, statsmodels for the forecasting engine, and rich for progress display. The local tabpfn-time-series package also needed to be installable.

## Status

**Completed**

## Problems Encountered

1. **hatch-vcs Version Resolution Error** (Discovered: 2026-02-06 16:15)
   - Status: Resolved
   - See: `2026-02-06_1600_to_2026-02-06_1700_dependency_setup_hatch_vcs_version_error.md`

## Goal Outcome

### Final State

All dependencies successfully added and installable via `uv sync`.

### Deliverables

**Modified Files:**

| File                                | Changes                                                                 |
| ----------------------------------- | ----------------------------------------------------------------------- |
| `pyproject.toml`                    | Added tabpfn>=6.0.6, gluonts>=0.16.0, statsmodels>=0.14.5, rich>=13.0.0 |
| `tabpfn-time-series/pyproject.toml` | Fixed hatch-vcs issue with static version="1.0.9"                       |

### Technical Debt

None.

### Follow-up Actions

None.
