# Problem: TabPFN LOCAL Mode Performance Bottleneck

**Goal:** Debug TabPFN Forecast Performance Issue
**Discovery Time:** 2026-02-05 11:37
**Status:** Identified (inherent characteristic, not a bug)

---

## Symptoms

**Observed Behaviors:**

- User's computer freezing during batch forecast runs
- Single company (RESTO - 1) took 7.7 minutes to forecast
- High CPU usage during TabPFN prediction
- Memory pressure (available memory dropped from 1.81 GB to minimal during processing)

**Example:**

- Processing time: 461 seconds for 74 accounts
- Average: ~6.2 seconds per account
- Memory usage started at 451.77 MB, dropped to 62.34 MB after completion

---

## Root Cause

TabPFN in LOCAL mode runs the neural network inference on the local CPU, which is computationally intensive. Each time series is processed sequentially, and the model requires significant compute resources for each prediction.

**Analysis:**

- TabPFN uses a transformer-based architecture for zero-shot forecasting
- LOCAL mode runs inference entirely on the user's machine
- With limited RAM (8 GB total, ~1.8 GB available), memory pressure causes system slowdowns
- Processing 74 accounts × 48 timesteps of history × 12 months forecast = significant computation
- No parallelization at the account level in the current implementation

---

## Evidence

### Log Excerpts

```
2026-02-05 11:52:32,891 - __main__ - INFO - SYSTEM INFO
2026-02-05 11:52:32,891 - __main__ - INFO - CPU count: 8 cores
2026-02-05 11:52:32,891 - __main__ - INFO - Total memory: 8.00 GB
2026-02-05 11:52:32,891 - __main__ - INFO - Available memory: 1.79 GB
```

```
Predicting time series:  32%|█▎  | 24/74 [01:04<01:45,  2.11s/it]
Predicting time series:  65%|██▌ | 48/74 [04:48<03:17,  7.61s/it]
Predicting time series: 100%|████| 74/74 [06:36<00:00,  5.36s/it]
```

```
2026-02-05 12:00:14,347 - src.forecasting.tabpfn_forecaster - INFO -   TabPFN forecast completed in 461.10s
2026-02-05 12:00:14,716 - __main__ - INFO -   Duration: 461.82s
2026-02-05 12:00:14,716 - __main__ - INFO -   Memory usage: 62.34 MB (Δ -389.42 MB)
```

### Performance Metrics

| Metric                   | Value          |
| ------------------------ | -------------- |
| Total forecast time      | 461.10 seconds |
| Accounts processed       | 74             |
| Average time per account | ~6.2 seconds   |
| Historical timesteps     | 48 months      |
| Forecast horizon         | 12 months      |
| Memory at start          | 451.77 MB      |
| Memory at end            | 62.34 MB       |
| Memory delta             | -389.42 MB     |

### Progress Timeline

| Progress     | Time Elapsed | Rate     |
| ------------ | ------------ | -------- |
| 24/74 (32%)  | 1:04         | 2.11s/it |
| 48/74 (65%)  | 4:48         | 7.61s/it |
| 74/74 (100%) | 6:36         | 5.36s/it |

**Note:** Processing time per account varies significantly (2.1s - 7.6s), likely depending on data characteristics (amount of history, NaN values, value ranges).

### Additional Evidence

Numerical overflow warnings indicate some accounts have extreme values:

```
RuntimeWarning: overflow encountered in cast
  x_inv[pos] = np.expm1(np.log(x[pos] * lmbda + 1) / lmbda)
RuntimeWarning: overflow encountered in expm1
  out[pos] = np.expm1(lmbda * np.log1p(x[pos])) / lmbda
```

---

## Solution

This is an inherent characteristic of TabPFN LOCAL mode, not a bug to fix. However, several mitigations are possible:

### Potential Approaches

1. **Use TabPFN CLIENT Mode** — Offload computation to remote TabPFN servers
   - Pros: Faster, no local resource constraints
   - Cons: Requires network, potential latency, API limits

2. **Reduce Context Length** — Use `max_context_length` parameter to limit history
   - Pros: Faster processing per account
   - Cons: May reduce forecast accuracy

3. **Batch Processing with Monitoring** — Process companies in small batches with memory checks
   - Pros: Prevents system freezing
   - Cons: Still slow overall

4. **Data Preprocessing** — Scale/normalize extreme values to reduce overflow warnings
   - Pros: May improve model performance, reduce warnings
   - Cons: Additional complexity

### Created Artifacts

1. **[debug_single_company.py](../../../debug_single_company.py)** — Script with comprehensive performance monitoring
   - System info logging (CPU, memory)
   - Per-step timing with PerformanceMonitor context manager
   - Memory delta tracking
   - Detailed logging output

2. **[PERFORMANCE_ANALYSIS.md](../../../PERFORMANCE_ANALYSIS.md)** — Documentation of performance characteristics and recommendations

---

## Follow-up Actions

**Remaining Tasks:**

- [ ] Evaluate TabPFN CLIENT mode as alternative
- [ ] Test with reduced `max_context_length` (e.g., 24 months instead of 48)
- [ ] Implement batch processing with memory monitoring for production use
- [ ] Add data preprocessing for extreme values to reduce overflow warnings
- [ ] Consider caching TabPFN model to reduce initialization overhead

**Known Limitations:**

- LOCAL mode will always be CPU-bound
- Memory-constrained systems (< 8 GB) may experience significant slowdowns
- Forecast time scales linearly with number of accounts
