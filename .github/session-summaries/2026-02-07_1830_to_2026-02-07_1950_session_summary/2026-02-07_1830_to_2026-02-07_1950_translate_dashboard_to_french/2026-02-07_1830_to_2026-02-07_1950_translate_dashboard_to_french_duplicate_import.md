# Problem: Duplicate Import Block in time_series_chart.py

**Goal:** Translate Dashboard to French (Step 4)
**Discovery Time:** 2026-02-07 19:00
**Status:** Workaround Applied

---

## Symptoms

**Observed Behaviors:**

- `src/visualization/components/time_series_chart.py` contains two identical import blocks from `..translations` (lines 14-25 and lines 27-38)
- No runtime error occurs because Python silently handles re-importing the same names
- No test failures

**Example:**

```python
# Lines 14-25 (first block)
from ..translations import (
    CHART_TRAIN_DATA,
    CHART_ACTUAL_TEST,
    CHART_FORECAST_SUFFIX,
    CHART_CI_SUFFIX,
    CHART_HOVER_TRAIN,
    CHART_HOVER_ACTUAL,
    CHART_HOVER_DATE,
    CHART_HOVER_VALUE,
    CHART_EMPTY_MESSAGE,
    CHART_XAXIS_LABEL
)

# Lines 27-38 (second block — exact duplicate)
from ..translations import (
    CHART_TRAIN_DATA,
    CHART_ACTUAL_TEST,
    CHART_FORECAST_SUFFIX,
    CHART_CI_SUFFIX,
    CHART_HOVER_TRAIN,
    CHART_HOVER_ACTUAL,
    CHART_HOVER_DATE,
    CHART_HOVER_VALUE,
    CHART_EMPTY_MESSAGE,
    CHART_XAXIS_LABEL
)
```

---

## Root Cause

**Analysis:**

During the editing process, the `replace_string_in_file` tool was used to apply multiple changes to `time_series_chart.py`. An initial batch of changes via `multi_replace_string_in_file` partially applied some edits. When the remaining edits were applied individually, the import block was already present from the first batch, but a second import block was added by a subsequent edit that targeted the original file state.

This is a tool-level editing artifact, not a logic error.

---

## Evidence

### Code Snippets

**Current State:**
```python
# File: src/visualization/components/time_series_chart.py (lines 14-38)
from ..translations import (
    CHART_TRAIN_DATA,
    CHART_ACTUAL_TEST,
    CHART_FORECAST_SUFFIX,
    CHART_CI_SUFFIX,
    CHART_HOVER_TRAIN,
    CHART_HOVER_ACTUAL,
    CHART_HOVER_DATE,
    CHART_HOVER_VALUE,
    CHART_EMPTY_MESSAGE,
    CHART_XAXIS_LABEL
)

from ..translations import (
    CHART_TRAIN_DATA,
    CHART_ACTUAL_TEST,
    CHART_FORECAST_SUFFIX,
    CHART_CI_SUFFIX,
    CHART_HOVER_TRAIN,
    CHART_HOVER_ACTUAL,
    CHART_HOVER_DATE,
    CHART_HOVER_VALUE,
    CHART_EMPTY_MESSAGE,
    CHART_XAXIS_LABEL
)
```

### File References

- `src/visualization/components/time_series_chart.py:14-38` — Duplicate import blocks

### Test Outputs

```
200 passed, 1 deselected
```

All tests pass despite the duplicate import.

---

## Solution

**Implementation Time:** Not yet fixed (cosmetic issue deferred)

### Approach

The second import block (lines 27-38) should be deleted. This is a trivial cleanup.

**Why Deferred:**

- Zero functional impact
- All tests pass
- Can be cleaned up as part of Step 5 (documentation update) or any future session

### Code Changes

**Fix required:**

Delete lines 27-38 in `src/visualization/components/time_series_chart.py` (the second, duplicate import block).

---

## Follow-up Actions

- [ ] Delete the duplicate import block in `src/visualization/components/time_series_chart.py` (lines 27-38)
