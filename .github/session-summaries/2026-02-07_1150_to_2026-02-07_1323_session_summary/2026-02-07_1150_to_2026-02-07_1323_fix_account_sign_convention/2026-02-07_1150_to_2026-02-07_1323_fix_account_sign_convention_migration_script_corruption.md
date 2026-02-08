# Problem: Migration Script Corrupted Prophet Data

**Goal:** Fix Account Sign Convention
**Discovery Time:** 2026-02-07 ~14:00
**Status:** Resolved

---

## Symptoms

**Observed Behaviors:**

- After running the migration script `scripts/migrate_sign_convention.py`, 73 `gather_result_corrected` files were created alongside Prophet `gather_result` files
- `data_loader.py` and `metrics/pipeline.py` were modified to prefer `gather_result_corrected` when loading data
- Upon review, the user questioned whether the "corrected" convention was actually needed

**Example:**

- Prophet account 707010 for RESTO - 1: original `gather_result` showed correct value **+69,706**
- After migration script: `gather_result_corrected` showed **-69,706** — the script had **flipped correct values to incorrect ones**

---

## Root Cause

**Analysis:**

- The migration script was based on the **incorrect assumption** that Prophet `gather_result` files had the same sign convention bug as the TabPFN preprocessing
- In reality, the sign convention issue existed **only** in `fec_to_monthly_totals()` in `src/data/preprocessing.py`, which is part of the TabPFN pipeline
- The Prophet pipeline (from the separate ProphetApproach codebase) has its own data processing that already handled signs correctly — revenue accounts (7xx) were already positive in Prophet data
- The migration script blindly multiplied all 7xx columns by -1, turning correct +69,706 into incorrect -69,706 for all 73 company Prophet forecasts

**Root Cause Pattern:** Overgeneralization — assuming a bug found in one pipeline (TabPFN preprocessing) applied to another pipeline (Prophet) without verification.

---

## Evidence

### Migration Script Logic (now deleted)

The script `scripts/migrate_sign_convention.py` contained logic that:
1. Found all `gather_result` files in Prophet process folders
2. Identified columns starting with '7' (revenue accounts)
3. Multiplied those columns by -1
4. Saved as `gather_result_corrected` alongside the original

### Data Verification

Prophet `gather_result` for RESTO - 1, account 707010:
- **Original value:** +69,706 (correct — revenue is positive)
- **After migration:** -69,706 (incorrect — migration flipped a correct value)

### Files Affected

- 73 `gather_result_corrected` files created (one per company) — all contained corrupted data
- `src/visualization/data_loader.py` — modified to prefer `gather_result_corrected` over `gather_result`
- `src/metrics/pipeline.py` — modified to prefer `gather_result_corrected` over `gather_result`

---

## Solution

**Implementation Time:** 2026-02-07 ~14:30

### Approach

Full cleanup: delete all corrupted files, revert code changes, delete the migration script.

**Why This Solution:**

- The migration was entirely based on a wrong assumption — there was no valid use case for `gather_result_corrected`
- Originals were preserved (the script created new files alongside), so no data was permanently lost
- The simplest and safest approach was complete removal

### Attempts Timeline

1. **Initial approach (wrong):** Create migration script to flip 7xx signs in Prophet data
   - **Result:** Corrupted 73 Prophet forecast files
   - **Reason:** Prophet data already had correct signs — the sign bug only existed in TabPFN preprocessing

2. **Final Solution:** Complete cleanup
   - **Result:** Success — all corrupted data removed, code reverted
   - **Reason:** The correct fix was preprocessing-only (already done); Prophet data should never be touched

### Code Changes

**Files Modified:**

1. `data/` — Deleted all 73 `gather_result_corrected` files
   - Command: `find data/ -name "gather_result_corrected" -type f -delete`

2. `src/visualization/data_loader.py` — Reverted to loading plain `gather_result`
   - Removed preference logic that checked for `gather_result_corrected` first
   - Confirmed: `git diff HEAD -- src/visualization/data_loader.py` shows zero changes vs last commit

3. `src/metrics/pipeline.py` — Reverted to loading plain `gather_result`
   - Same reversion as data_loader.py
   - Confirmed: `git diff HEAD -- src/metrics/pipeline.py` shows zero changes vs last commit

4. `scripts/migrate_sign_convention.py` — Deleted entirely
   - Confirmed: `ls scripts/migrate_sign_convention.py` returns "No such file or directory"

### Validation

**Verification Methods:**

- `find data/ -name "gather_result_corrected" -type f | wc -l` returns 0
- `ls scripts/migrate_sign_convention.py` returns "No such file or directory"
- `git diff HEAD -- src/visualization/data_loader.py src/metrics/pipeline.py` returns empty (no diff)
- Prophet data integrity confirmed: account 707010 value is still +69,706 in original `gather_result`
- 21 tests in modified modules all pass

---

## Follow-up Actions

**Key Lesson for Future Sessions:**

> **Never modify Prophet `gather_result` files.** The Prophet pipeline (ProphetApproach) has its own correct data processing. Only the TabPFN preprocessing (`fec_to_monthly_totals()`) is in our control. When a bug is found in TabPFN preprocessing, fix it there and re-run TabPFN — do not "fix" Prophet data to match.

**Known Limitations:**

- No automated guard prevents modification of Prophet data files. Vigilance is required.

**Related Issues:**

- This cleanup has implications for Step 5 (Documentation): the plan originally mentioned documenting the `gather_result_corrected` migration approach — that reference was updated in the plan file to reflect this correction.
