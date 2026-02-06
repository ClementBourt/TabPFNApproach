# Goal: Data Conversion Module

**Session Period:** 2026-02-06 16:20 to 2026-02-06 16:30

## Objective

Create a module to convert between the preprocessing wide-format data (ds index × account columns) and the TabPFN input/output format (timestamp, target, item_id).

## Motivation

The preprocessing module outputs data in wide format, but TabPFN expects a long format with specific columns. A bidirectional converter is needed to:

1. Transform preprocessed data into TabPFN input format
2. Transform TabPFN forecast output back to wide format for saving

## Status

**Completed**

## Problems Encountered

None.

## Goal Outcome

### Final State

The data_converter module provides two functions for seamless format conversion with full test coverage.

### Deliverables

**New Files Created:**

| File                                            | Purpose                     |
| ----------------------------------------------- | --------------------------- |
| `src/forecasting/data_converter.py`             | Format conversion functions |
| `tests/unit/forecasting/test_data_converter.py` | 10 unit tests               |

**Key Functions:**

- `wide_to_tabpfn_format(wide_df)` → Converts wide DataFrame to TabPFN format
- `tabpfn_output_to_wide_format(tabpfn_output, column_name)` → Converts TabPFN output back to wide format

### Technical Debt

None.

### Follow-up Actions

None.
