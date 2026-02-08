# Problem: Sign Convention Bug in Preprocessing

**Goal:** Fix Account Sign Convention
**Discovery Time:** 2026-02-07 11:50
**Status:** Resolved

---

## Symptoms

**Observed Behaviors:**

- Account 707010 (revenue) for RESTO - 1 displayed **negative** values in the TabPFN training data and forecasts
- The existing test `test_fec_to_monthly_totals_calculates_solde_correctly` explicitly asserted that revenue was negative (`assert (revenue_solde < 0).all()`) — the test encoded the bug as expected behavior
- Dashboard aggregated "Net Income" view was confusing because revenue was flipped

**Example:**

- Account 707010 showed values like -75,481.77 instead of +75,481.77 in TabPFN `gather_result`

---

## Root Cause

**Analysis:**

- `src/data/preprocessing.py`, function `fec_to_monthly_totals()`, line 254 (at commit `a9af2c5`) applied a single formula `Solde = Debit - Credit` to **all** accounts uniformly
- For expense accounts (6xx), this is correct: expenses are recorded as debits, so `Debit - Credit > 0`
- For revenue accounts (7xx), this is incorrect: revenue is recorded as credits, so `Debit - Credit < 0`. The correct formula for revenue is `Credit - Debit > 0`
- The original code commented "Revenue accounts (7xx) will naturally have negative values (more credit than debit)" — treating the negative sign as a feature rather than a bug

**Note:** This only affected the TabPFN pipeline. The Prophet pipeline (from the ProphetApproach codebase) has its own independent data processing that already handled signs correctly.

---

## Evidence

### Code Snippets

**Before (Commit a9af2c5):**
```python
# File: src/data/preprocessing.py (lines 251-258)
    # Calculate balance (Solde = Debit - Credit for expenses, Credit - Debit for revenue)
    # For simplicity, we use the standard convention: Solde = Debit - Credit
    # Revenue accounts (7xx) will naturally have negative values (more credit than debit)
    filtered_fecs['Solde'] = filtered_fecs['Debit'] - filtered_fecs['Credit']

    # Handle empty DataFrame case
    if filtered_fecs.empty:
        return pd.DataFrame(columns=['PieceDate', 'CompteNum', 'Solde'])
```

**After (Current state):**
```python
# File: src/data/preprocessing.py (lines 252-271)
    # Handle empty DataFrame case early
    if filtered_fecs.empty:
        return pd.DataFrame(columns=['PieceDate', 'CompteNum', 'Solde'])

    # Calculate balance using account-aware sign convention
    # Revenue accounts (7xx): Solde = Credit - Debit (positive values)
    # Expense accounts (6xx): Solde = Debit - Credit (positive values)
    # This ensures both revenue and expenses have positive values for easier interpretation
    
    def calculate_solde(row: pd.Series) -> float:
        """Calculate Solde based on account type."""
        if row['CompteNum'].startswith('7'):
            # Revenue: Credit - Debit (positive when credit > debit)
            return row['Credit'] - row['Debit']
        else:
            # Expenses: Debit - Credit (positive when debit > credit)
            return row['Debit'] - row['Credit']
    
    filtered_fecs['Solde'] = filtered_fecs.apply(calculate_solde, axis=1)
```

### Test Changes

**Before (Commit a9af2c5):**
```python
# File: tests/unit/data/test_preprocessing.py (lines 397-407)
def test_fec_to_monthly_totals_calculates_solde_correctly(sample_formatted_fecs):
    """Test that Solde is calculated as Debit - Credit."""
    result = fec_to_monthly_totals(sample_formatted_fecs)
    
    # Revenue accounts should have negative solde (Credit > Debit)
    revenue_solde = result[result['CompteNum'] == '707000']['Solde']
    assert (revenue_solde < 0).all()
    
    # Expense accounts should have positive solde (Debit > Credit)
    expense_solde = result[result['CompteNum'] == '601000']['Solde']
    assert (expense_solde > 0).all()
```

**After (Current state):**
```python
# File: tests/unit/data/test_preprocessing.py (lines 397-413)
def test_fec_to_monthly_totals_calculates_solde_correctly(sample_formatted_fecs):
    """
    Test that Solde is calculated with account-aware sign convention.
    
    Revenue accounts (7xx): Solde = Credit - Debit (should be positive)
    Expense accounts (6xx): Solde = Debit - Credit (should be positive)
    """
    result = fec_to_monthly_totals(sample_formatted_fecs)
    
    # Revenue accounts (7xx) should have POSITIVE solde (Credit > Debit, so Credit - Debit > 0)
    revenue_solde = result[result['CompteNum'] == '707000']['Solde']
    assert (revenue_solde > 0).all(), "Revenue accounts (7xx) should have positive values"
    
    # Expense accounts (6xx) should have POSITIVE solde (Debit > Credit, so Debit - Credit > 0)
    expense_solde = result[result['CompteNum'] == '601000']['Solde']
    assert (expense_solde > 0).all(), "Expense accounts (6xx) should have positive values"
```

**New test added:**
```python
# File: tests/unit/data/test_preprocessing.py (lines 416-460)
def test_fec_to_monthly_totals_sign_convention_various_accounts():
    """
    Test sign convention for various specific revenue and expense accounts.
    """
    test_data = []
    base_date = pd.Timestamp('2023-01-15')
    
    revenue_accounts = ['707000', '707010', '708000', '709000']
    for account in revenue_accounts:
        test_data.append({
            'PieceDate': base_date, 'CompteNum': account,
            'Debit': 0.0, 'Credit': 1000.0
        })
    
    expense_accounts = ['601000', '602000', '606000', '611000', '613000']
    for account in expense_accounts:
        test_data.append({
            'PieceDate': base_date, 'CompteNum': account,
            'Debit': 500.0, 'Credit': 0.0
        })
    
    test_fecs = pd.DataFrame(test_data)
    result = fec_to_monthly_totals(test_fecs)
    
    for account in revenue_accounts:
        account_solde = result[result['CompteNum'] == account]['Solde'].iloc[0]
        assert account_solde > 0
        assert account_solde == 1000.0
    
    for account in expense_accounts:
        account_solde = result[result['CompteNum'] == account]['Solde'].iloc[0]
        assert account_solde > 0
        assert account_solde == 500.0
```

### File References

- `src/data/preprocessing.py:251-271` — Account-aware `calculate_solde()` function (current state)
- `tests/unit/data/test_preprocessing.py:397-460` — Updated + new sign convention tests

### Additional Evidence: Edge case fix

The empty DataFrame check was moved **before** the `.apply()` call. In the original code (commit `a9af2c5`), the check was after the Solde calculation at line 257, which was fine for a simple column assignment. But with `.apply()`, an empty DataFrame would cause a `ValueError`. Moving the check to line 252 prevents this.

---

## Solution

**Implementation Time:** 2026-02-07 ~12:30

### Approach

Replaced the single `Debit - Credit` formula with an account-aware `calculate_solde()` function that checks whether the account starts with '7' (revenue) or not (expense/other) and applies the appropriate formula.

**Why This Solution:**

- Minimal change scope — only the `fec_to_monthly_totals()` function needed modification
- Clear, readable logic with comments explaining the convention
- Defensive: empty DataFrame handled before `.apply()` to prevent runtime errors

### Code Changes

**Files Modified:**

1. `src/data/preprocessing.py` — Replaced `filtered_fecs['Solde'] = filtered_fecs['Debit'] - filtered_fecs['Credit']` with `calculate_solde()` function using `.apply(axis=1)`, moved empty check before computation
2. `tests/unit/data/test_preprocessing.py` — Updated existing test assertions (`< 0` → `> 0` for revenue), added new comprehensive test covering 9 accounts

### Validation

**Verification Methods:**

- TDD red phase: Tests written first, confirmed to fail with old code
- TDD green phase: Tests pass after fix
- TabPFN re-run for RESTO - 1: 70 accounts forecasted in 503.6 seconds
- Account 707010 confirmed positive: +75,481.77

**Test Results:**

```
187 passed, 1 failed (pre-existing: test_tabpfn_forecaster_initialization_with_client_mode — browser auth issue, unrelated)
```

**TabPFN Re-run:**

```
process_id: 42f3aab4-35fe-42ff-a88a-f7b3083cd32f
Accounts forecasted: 70
Duration: 503.6 seconds
Account 707010 value: +75,481.77 (was -75,481.77)
```

---

## Follow-up Actions

- [ ] Step 3 will require another TabPFN re-run (current `gather_result` has no quantile data for CI bands)
- [ ] Consider vectorizing `calculate_solde()` with `np.where()` for performance
