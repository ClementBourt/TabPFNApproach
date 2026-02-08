# Dashboard Iterative Improvements Plan (4 Steps)

## Status Tracking

| Step | Description                          | Status      | Session Date | Notes for Next Session |
|------|--------------------------------------|-------------|--------------|------------------------|
| 1    | Rename "FirstTry" → "ProphetWorkflow" | ✅ DONE     | Feb 7, 2026  | All 73 company.json files updated. Migration script created at scripts/rename_firsttry.py. No "FirstTry" remains in data/. 2 new tests added. All 178 tests pass. |
| 2    | Fix account sign convention          | ✅ DONE     | Feb 7, 2026  | Preprocessing fixed with account-aware sign logic (7xx: Credit-Debit, 6xx: Debit-Credit). 2 tests added (23 total in test_preprocessing.py). TabPFN re-run for RESTO-1 (process_id: 42f3aab4-35fe-42ff-a88a-f7b3083cd32f) with correct signs. Prophet data was already correct — no migration needed. A migration script that incorrectly flipped Prophet signs was created and deleted (see Lessons Learned). 187/188 tests pass (1 pre-existing: client-mode browser auth). |
| 3    | Add TabPFN confidence intervals      | ✅ DONE     | Feb 7, 2026  | End-to-end CI pipeline implemented. `extract_quantiles_from_tabpfn_output()` in data_converter.py now resolves alternate quantile column names. `ForecastResult` extended with `forecast_lower_df`/`forecast_upper_df`. `BatchProcessor` saves `gather_result_lower`/`gather_result_upper` via `save_forecast_result_with_ci()`. Data loader, callbacks, and chart already wired for CI bands. TabPFN re-run for RESTO-1 (process_id: f83f2ed0-6955-4fa8-8af2-e334cdac9cd1) with 70 accounts, all 3 CI files saved. 9 new/updated tests across test_data_converter.py, test_tabpfn_forecaster.py, test_result_loader.py, test_batch_processor.py. 200/201 tests pass (1 pre-existing: client-mode browser auth). Log at /tmp/tabpfn_forecast_20260207_172433.log. |
| 4    | Translate dashboard to French        | ✅ DONE     | Feb 7, 2026  | Complete French translation implemented. Created translations.py with all French strings. Refactored aggregation keys to internal English (net_income, total_revenue, total_expenses, total_activity) with French display labels via AGG_LABELS mapping. Updated all 8 visualization files (app.py, layouts.py, callbacks.py, data_loader.py, time_series_chart.py, metrics_table.py). Updated 6 tests in test_data_loader.py to use internal keys and expect French labels. "Forecast" remains in English per requirements. All 200/201 tests pass (1 pre-existing: client-mode browser auth). |
| 5    | Update documentation                 | ✅ DONE     | Feb 7, 2026  | DASHBOARD_README.md and DASHBOARD_IMPLEMENTATION.md updated to reflect all 4 improvements: ProphetWorkflow rename, sign convention, CI bands, French UI. Architecture diagrams updated with translations.py and scripts/. Test counts updated to 200+. |

---

## Decisions Made

- **Execution order**: 1→2→3→4 (rename → sign fix → CI → translation) to minimize rework
- **Sign fix approach**: Fix preprocessing only (`fec_to_monthly_totals()`) + re-run TabPFN. Prophet data already had correct signs — no migration needed.
- **Re-run scope**: RESTO - 1 only
- **CI quantiles**: Keep existing 0.1/0.9 (80% CI)
- **French keys**: Decoupled — internal English keys, French display labels
- **Documentation updates**: After implementation, not before

---

## Step 1 — Rename "FirstTry" → "ProphetWorkflow"

**Scope**: Pure data/string rename. Lowest risk, no logic changes.

**Files to modify**:
- All `company.json` files under `data/` (~50+ files) — replace `"FirstTry"` with `"ProphetWorkflow"` in both `version_name` and `description` fields
- `src/visualization/data_loader.py` (L123) — update docstring example
- `DASHBOARD_IMPLEMENTATION.md` (L145) — update reference to "FirstTry"

**Approach**:
1. Write a Python migration script (`scripts/rename_firsttry.py`) that uses `pathlib` + `json` to find all `company.json` files and replace `"FirstTry"` → `"ProphetWorkflow"`
2. Run the script
3. Update docstring in `data_loader.py`
4. Write a test (or run the script in dry-run mode) to verify all `company.json` files have been updated

**Acceptance criteria**:
- `grep -r "FirstTry" data/` returns zero matches
- Dashboard loads and shows "ProphetWorkflow" in chart legends and metrics table
- Existing tests pass

**Tests**: Add a test that loads RESTO - 1's `company.json` and asserts `"ProphetWorkflow"` appears.

---

## Step 2 — Fix Account Sign Convention

**Scope**: Preprocessing fix in `fec_to_monthly_totals()` + TabPFN re-run.

**Root cause**: `src/data/preprocessing.py` (L254) applied `Debit - Credit` uniformly. Revenue accounts (7xx) should use `Credit - Debit` so their values are positive. This only affected the TabPFN pipeline (which uses `fec_to_monthly_totals()`). Prophet data from the ProphetApproach pipeline already had correct sign conventions.

**What was done**:

1. **TDD — Red phase**: Updated `test_fec_to_monthly_totals_calculates_solde_correctly` to assert revenue is positive. Added `test_fec_to_monthly_totals_sign_convention_various_accounts` covering accounts 707000, 707010, 708000, 709000, 601000, 602000, 606000, 611000, 613000. Confirmed tests fail.
2. **Fix preprocessing**: In `fec_to_monthly_totals()`, added `calculate_solde()` function:
   - If `CompteNum` starts with `'7'`: `Solde = Credit - Debit`
   - Otherwise: `Solde = Debit - Credit`
   - Moved empty DataFrame check BEFORE `.apply()` to fix edge case `ValueError`
3. **TDD — Green phase**: All 23 preprocessing tests pass.
4. **Re-ran TabPFN** for RESTO - 1 → process_id: `42f3aab4-35fe-42ff-a88a-f7b3083cd32f`. Account 707010 now shows +75,482 (correct positive revenue).
5. **Verified**: 187/188 tests pass. Prophet data untouched and still correct (+69,706 for account 707010).

**Mistake made & corrected**:
A migration script (`scripts/migrate_sign_convention.py`) was initially created to flip 7xx signs in Prophet `gather_result` files, producing `gather_result_corrected` alongside originals. `data_loader.py` and `metrics/pipeline.py` were updated to prefer `gather_result_corrected`. This was **wrong** — Prophet data already had correct signs, so the script corrupted 73 files (flipping correct +69,706 → incorrect -69,706). **Cleanup**: All 73 `gather_result_corrected` files deleted, `data_loader.py` and `pipeline.py` reverted, migration script deleted. Prophet data integrity confirmed.

**Files modified (final state)**:
- `src/data/preprocessing.py` — account-aware `calculate_solde()` in `fec_to_monthly_totals()`
- `tests/unit/data/test_preprocessing.py` — 1 test updated + 1 new test (23 total)

**Files NOT modified (confirmed correct as-is)**:
- `src/visualization/data_loader.py` — loads plain `gather_result`, no changes needed
- `src/metrics/pipeline.py` — loads plain `gather_result`, no changes needed
- Prophet `gather_result` files — already had correct signs

### Lessons Learned from Step 2 → Implications for Step 3

1. **TabPFN must be re-run again for Step 3**: The current TabPFN `gather_result` only contains median forecasts. Step 3 needs quantile data (`gather_result_lower`, `gather_result_upper`) saved alongside — this requires updating the saver before re-running. Running for all 73 companies will take ~6+ hours.
2. **Manual package install required**: `tabpfn-time-series` is a local editable install not tracked in `pyproject.toml`. Run `uv pip install -e ./tabpfn-time-series/` before any forecasting work.
3. **Prophet data must not be touched**: The Prophet pipeline (ProphetApproach) has its own data processing. Only TabPFN preprocessing (`fec_to_monthly_totals()`) is in our control. Never modify Prophet `gather_result` files.
4. **Handle `None` gracefully**: When Prophet has no CI data, the chart/loader must skip CI rendering without errors. Design for this from the start.
5. **Pre-existing test failure**: `test_tabpfn_forecaster_initialization_with_client_mode` fails due to browser-based auth — this is unrelated and can be ignored.

---

## Step 3 — Add TabPFN Confidence Intervals

**Scope**: End-to-end pipeline change from forecasting output through to dashboard rendering.

**Current state**: TabPFN forecasts with quantiles `[0.1, 0.5, 0.9]` (`src/forecasting/tabpfn_forecaster.py` L109), but quantile data is dropped in `src/forecasting/data_converter.py` (L131-L136) during the `tabpfn_output_to_wide_format()` pivot.

**Files to modify**:
- `src/forecasting/data_converter.py` (L131-L136) — extend `tabpfn_output_to_wide_format()` to also extract quantile columns into separate DataFrames (lower/upper)
- `src/forecasting/tabpfn_forecaster.py` — extend `ForecastResult` (if it exists as a dataclass) to carry `forecast_lower_df` and `forecast_upper_df`
- `src/forecasting/result_saver.py` — save quantile DataFrames as `gather_result_lower` and `gather_result_upper` alongside `gather_result`
- `src/metrics/result_loader.py` — add function to load quantile files
- `src/visualization/data_loader.py` — extend `DashboardData` to hold `forecast_lower` and `forecast_upper` dicts
- `src/visualization/components/time_series_chart.py` (L80-L95) — add shaded `go.Scatter` traces with `fill='tonexty'` for the 10th-90th percentile band
- `src/visualization/callbacks.py` — pass CI data through to chart function

**Approach**:
1. **Investigate TabPFN output format**: Run a quick test prediction to inspect the actual column names returned by `predict_df()` with quantiles. This is critical — the exact column names (`q_0.1`, `quantile_0.1`, etc.) are unknown from code alone.
2. **Test first**: Write tests for the new converter behavior, chart rendering with CI bands
3. **Extend data pipeline**: Modify converter → saver → loader chain to preserve quantile data
4. **Re-run TabPFN** for RESTO - 1 (Step 2 already re-ran TabPFN, but the current saver drops quantile data → must re-run again with the updated saver)
5. **Render CI bands**: Add two new `go.Scatter` traces per approach that has CI data — one for upper bound (transparent), one for lower bound with `fill='tonexty'` to shade the area between. Use a lighter/transparent version of the approach color.
6. **Handle Prophet gracefully**: Prophet has no CI data → chart function should skip CI rendering when lower/upper DataFrames are `None`

**Acceptance criteria**:
- TabPFN forecast on the dashboard shows a shaded 80% confidence band behind the point forecast line
- Prophet forecast shows no band (graceful absence)
- CI band is visible for both individual accounts and aggregated views
- Hover on CI band shows meaningful tooltip

**Risks**:
- The TabPFN `predict_df()` output format must be verified empirically
- If Step 2 already re-ran TabPFN, the forecast files won't have CI data yet → must re-run again with the updated saver

---

## Step 4 — Translate Dashboard to French

**Scope**: All user-facing strings translated to French. "Forecast" stays in English per the user's instruction.

**Files to modify** (comprehensive list):
- `src/visualization/layouts.py` — header, subtitle, footer, selector label (~4 strings)
- `src/visualization/callbacks.py` — error messages, titles, labels (~12 strings)
- `src/visualization/components/time_series_chart.py` — trace names, hover templates, empty message (~8 strings)
- `src/visualization/components/metrics_table.py` — metric descriptions, column headers, note text, empty message (~10 strings)
- `src/visualization/data_loader.py` (L323-L344) — dropdown labels and section headers (~8 strings)
- `src/visualization/app.py` (L76) — page title

**Key design — Decouple internal keys from French display labels**:

Introduce a translation/mapping layer. The dropdown values (e.g., `AGG:net_income`) and `get_aggregated_series()` will use **internal English keys** (`net_income`, `total_revenue`, `total_expenses`, `total_activity`). Display labels will be French (`Résultat Net`, `Chiffre d'Affaires Total`, `Total Charges`, `Activité Totale`). The `agg_key_mapping` in `callbacks.py` (L159-L164) becomes the single source mapping internal keys to both aggregation logic and French labels.

**Approach**:
1. **Create a translation constants file** `src/visualization/translations.py` containing all French strings, organized by component. This centralizes translations and makes future i18n easier.
2. **Refactor aggregation keys**: Change dropdown values from `AGG:Net Income` → `AGG:net_income`, update `get_aggregated_series()` to accept internal keys, update `agg_key_mapping`
3. **Replace strings** in all 6 files listed above, importing from the translations module
4. **Update tests** — the existing 25 tests reference English strings; update assertions to match French labels
5. **Test visually** — launch dashboard and verify all text is French, "Forecast" remains English

**Acceptance criteria**:
- All visible dashboard text is in French
- The word "Forecast" appears in English everywhere it's used
- Internal logic uses stable English keys
- All 25+ tests pass (updated to expect French strings)

**Strings that stay in English**: "Forecast", "TabPFN", "ProphetWorkflow", metric acronyms (MAPE, SMAPE, etc.), "Dash", "Date"

### Detailed String Inventory

#### `layouts.py`
| Line | Current | French |
|------|---------|--------|
| L37 | `"Forecast Comparison Dashboard"` | `"Tableau de Bord de Comparaison des Forecasts"` |
| L47 | `f"Company: {display_name}"` | `f"Entreprise : {display_name}"` |
| L72 | `"Select Account or Aggregated View:"` | `"Sélectionner un Compte ou une Vue Agrégée :"` |
| L143 | `"TabPFN vs Prophet Forecast Comparison \| Built with Dash"` | `"Comparaison des Forecasts TabPFN vs Prophet \| Construit avec Dash"` |

#### `callbacks.py`
| Line | Current | French |
|------|---------|--------|
| L63 | `"Please select an account or aggregated view"` | `"Veuillez sélectionner un compte ou une vue agrégée"` |
| L79 | `f"{agg_type} - Forecast Comparison"` | `f"{agg_type} - Comparaison des Forecasts"` |
| L80 | `"Amount (€)"` | `"Montant (€)"` |
| L83 | `f"Error computing aggregation: {str(e)}"` | `f"Erreur de calcul de l'agrégation : {str(e)}"` |
| L90 | `f"Account {account} not found"` | `f"Compte {account} introuvable"` |
| L101 | `f"No forecasts available for account {account}"` | `f"Aucun forecast disponible pour le compte {account}"` |
| L103 | `f"Account {account} - Forecast Comparison"` | `f"Compte {account} - Comparaison des Forecasts"` |
| L126 | `"Please select an account or aggregated view"` | (same as L63) |
| L170 | `f"Error computing metrics: {str(e)}"` | `f"Erreur de calcul des métriques : {str(e)}"` |
| L172 | `f"Metrics Comparison - {agg_type}"` | `f"Comparaison des Métriques - {agg_type}"` |
| L180 | `f"Account {account} not found"` | (same as L90) |
| L201 | `f"Metrics Comparison - Account {account}"` | `f"Comparaison des Métriques - Compte {account}"` |
| L205 | `"No metrics available for this selection"` | `"Aucune métrique disponible pour cette sélection"` |

#### `time_series_chart.py`
| Line | Current | French |
|------|---------|--------|
| L62 | `name='Train Data'` | `name='Données d\'Entraînement'` |
| L65-67 | `hovertemplate='<b>Train</b>...'` | `hovertemplate='<b>Entraînement</b>...'` |
| L74 | `name='Actual (Test)'` | `name='Réel (Test)'` |
| L77 | `hovertemplate='<b>Actual</b>...'` | `hovertemplate='<b>Réel</b>...'` |
| L86 | `name=f'{approach_name} Forecast'` | `name=f'Forecast {approach_name}'` |
| L89 | `hovertemplate 'Date: ... Value: ...'` | `'Date : ... Valeur : ...'` |
| L109 | `"No data available"` | `"Aucune donnée disponible"` |

#### `metrics_table.py`
| Line | Current | French |
|------|---------|--------|
| L17-L23 | Metric full names | French equivalents |
| L88 | Column header `'Metric'` | `'Métrique'` |
| L79 | `"No metrics available"` | `"Aucune métrique disponible"` |
| L186 | `"Note: Lower values are better..."` | `"Note : Des valeurs plus basses sont meilleures..."` |
| L196 | `"Metrics Comparison"` | `"Comparaison des Métriques"` |

#### `data_loader.py`
| Line | Current | French |
|------|---------|--------|
| L323 | `'─── Aggregated Views ───'` | `'─── Vues Agrégées ───'` |
| L329-332 | `"Net Income"`, `"Total Revenue"`, `"Total Expenses"`, `"Total Activity"` | `"Résultat Net"`, `"Chiffre d'Affaires Total"`, `"Total Charges"`, `"Activité Totale"` |
| L338 | `'─── Individual Accounts ───'` | `'─── Comptes Individuels ───'` |
| L344 | `f"Account {account}"` | `f"Compte {account}"` |

#### `app.py`
| Line | Current | French |
|------|---------|--------|
| L76 | `app.title = f"Forecast Comparison - {company_id}"` | `f"Comparaison des Forecasts - {company_id}"` |

---

## Step 5 — Update Documentation

**Scope**: Update `DASHBOARD_README.md` and `DASHBOARD_IMPLEMENTATION.md` to reflect all changes.

**When**: After all 4 implementation steps are complete.

**What to update in `DASHBOARD_README.md`** (user-facing):
-  All example screenshots/descriptions should reference French UI
- Document the ProphetWorkflow rename
- Document the confidence interval feature
- Update metrics table if any descriptions changed
- Document correct sign convention behavior
- Update CLI examples if any changed

**What to update in `DASHBOARD_IMPLEMENTATION.md`** (implementation-focused):
- Document the sign convention fix (preprocessing-only, no migration)
- Document the confidence interval pipeline (converter → saver → loader → chart)
- Document the translation architecture (translations.py, key/label decoupling)
- Update code quality section with new test counts
- Update the architecture diagram with new files (`translations.py`, `scripts/`)

---

## Verification Checklist (After All Steps Complete)

- [x] Account 707010 shows positive values (verified for both Prophet and TabPFN)
- [x] `grep -r "FirstTry" data/` returns zero matches
- [x] No `gather_result_corrected` files remain in `data/`
- [x] `uv run pytest tests/ -v` — 200/201 pass (1 pre-existing: client-mode browser auth)
- [ ] Dashboard launches: `uv run python -m src.visualization.cli dashboard`
- [ ] All dashboard text is in French (except "Forecast", "TabPFN", "ProphetWorkflow", metric acronyms)
- [ ] "Net Income" aggregation shows correct positive/negative pattern
- [ ] TabPFN forecast shows 80% confidence band
- [ ] Prophet forecast shows no confidence band (graceful)
- [ ] Chart legend shows "ProphetWorkflow" (not "FirstTry")
- [ ] `DASHBOARD_README.md` and `DASHBOARD_IMPLEMENTATION.md` are up to date

---

## Dependencies Between Steps

| Pair   | Dependency? | Details |
|--------|-------------|---------|
| 1 ↔ 2 | NO          | Independent |
| 1 ↔ 3 | NO          | Independent |
| 1 ↔ 4 | WEAK        | Renamed "ProphetWorkflow" label will appear in French UI |
| 2 ↔ 3 | YES         | If sign convention is fixed, stored TabPFN CI data also needs correct signs |
| 2 ↔ 4 | YES         | Both touch `data_loader.py` and `callbacks.py`; sign fix changes what aggregations compute |
| 3 ↔ 4 | YES         | New CI traces need French legend labels |
