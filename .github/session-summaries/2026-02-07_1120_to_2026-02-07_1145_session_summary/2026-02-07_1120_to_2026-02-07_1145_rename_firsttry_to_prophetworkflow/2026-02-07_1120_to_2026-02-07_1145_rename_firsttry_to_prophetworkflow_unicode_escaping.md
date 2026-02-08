# Problem: Unicode Escape Sequences Converted to Literal UTF-8

**Goal:** Rename "FirstTry" to "ProphetWorkflow" Across Codebase
**Discovery Time:** 2026-02-07 11:30
**Status:** Resolved (by design)

---

## Symptoms

**Observed Behaviors:**

- After running `scripts/rename_firsttry.py`, the git diff for each `company.json` file was unexpectedly large
- Beyond the expected 2-line change (`version_name` and `description`), approximately 40-70 additional lines showed changes in the `account_number_name_map` section
- The additional changes were all of the form: `\uXXXX` escape sequences replaced with literal UTF-8 characters (e.g., `\u00e9` became `é`, `\u00e0` became `à`)

**Example:**

```diff
-    "623600": "Catalogues et imprim\u00e9s",
+    "623600": "Catalogues et imprimés",
```

---

## Root Cause

**Analysis:**

- The original `company.json` files were written with `json.dump` using the default `ensure_ascii=True`, which encodes non-ASCII characters as `\uXXXX` escape sequences
- The migration script (`scripts/rename_firsttry.py`) used `json.dump` with `ensure_ascii=False` to preserve the readability of French characters (accented letters like é, è, à, ê, etc.)
- When Python's `json.load()` reads `\u00e9`, it decodes it to the Python string `é`. When `json.dump` writes it back with `ensure_ascii=False`, it writes the literal character `é` instead of re-escaping it

**Root cause confirmed:** This is expected Python JSON behavior, not a bug. Both representations are semantically identical JSON.

---

## Evidence

### Code Snippet

```python
# File: scripts/rename_firsttry.py (lines 87-90)
if not dry_run:
    # Write back to file with proper formatting
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(updated_data, f, indent=2, ensure_ascii=False)
        f.write('\n')  # Add trailing newline
```

### Git Diff Excerpt (data/RESTO - 1/company.json)

```diff
@@ -12,8 +12,8 @@
   "forecast_versions": [
     {
-      "version_name": "FirstTry",
-      "description": "FirstTry",
+      "version_name": "ProphetWorkflow",
+      "description": "ProphetWorkflow",
...
@@ -1223,74 +1223,74 @@
   "account_number_name_map": {
-    "623600": "Catalogues et imprim\u00e9s",
+    "623600": "Catalogues et imprimés",
-    "647500": "M\u00e9decine du travail, pharmacie",
+    "647500": "Médecine du travail, pharmacie",
```

### File References

- `scripts/rename_firsttry.py:87-90` — The `json.dump` call with `ensure_ascii=False`
- `data/RESTO - 1/company.json:1223-1296` — The `account_number_name_map` section affected

---

## Solution

**Implementation Time:** 2026-02-07 11:30

### Approach

No fix was needed. The `ensure_ascii=False` parameter was intentionally chosen because:

1. The French account names are **more readable** with literal UTF-8 characters (`"Médecine du travail"` vs `"M\u00e9decine du travail"`)
2. Both representations are **semantically identical** in JSON
3. The files are already saved with UTF-8 encoding
4. This is a one-time diff noise; future edits to these files will not re-trigger the change

### Alternatives Considered

1. **Use `ensure_ascii=True`:** Would avoid diff noise but sacrifice readability of French text. Rejected because readability matters for a French accounting project.
2. **Only write files where `version_name` changed:** Would have required more complex logic and still needed a decision about `ensure_ascii`. Rejected as over-engineering.

### Validation

**Verification Methods:**

- Confirmed all 73 files parse correctly with `json.load()`
- Verified French characters render correctly in the dashboard
- All 178 tests pass, including the 2 new `TestProphetWorkflowRename` tests

---

## Follow-up Actions

None required. This is a resolved cosmetic issue.
