# Problem: hatch-vcs Version Resolution Error

**Goal:** TabPFN Forecasting Pipeline Implementation
**Discovery Time:** 2026-02-06 16:15
**Status:** Resolved

---

## Symptoms

**Observed Behaviors:**

- `uv sync` failed when trying to install `tabpfn-time-series` package
- Error message indicated setuptools-scm could not detect version
- Build backend `hatchling` failed with exit status 1

**Error Message:**

```
LookupError: Error getting the version from source
`vcs`: setuptools-scm was unable to detect version for
/Users/Bourtguize-Ramel/Desktop/bobbee/analysis-forecasting/TabPFNApproach/tabpfn-time-series.

However, a repository was found in a parent directory:
/Users/Bourtguize-Ramel/Desktop/bobbee/analysis-forecasting/TabPFNApproach
```

---

## Root Cause

The `tabpfn-time-series` package uses `hatch-vcs` for dynamic version management, which relies on git tags to determine the package version. The `tabpfn-time-series` folder is a subfolder of the main TabPFNApproach repository, not its own git repository.

`hatch-vcs` requires either:

1. The package directory to be a git repository root
2. Explicit configuration to search parent directories
3. The root to be explicitly set

Since the subfolder is not a standalone git repository, the version lookup failed.

---

## Evidence

### Log Excerpts

```
× Failed to build `tabpfn-time-series @
file:///Users/Bourtguize-Ramel/Desktop/bobbee/analysis-forecasting/TabPFNApproach/tabpfn-time-series`
├─▶ The build backend returned an error
╰─▶ Call to `hatchling.build.prepare_metadata_for_build_wheel` failed (exit status: 1)
```

### File References

- `tabpfn-time-series/pyproject.toml:35-36` — Version source configuration causing the issue

### Code Before Fix

```toml
# File: tabpfn-time-series/pyproject.toml (lines 1-7, 35-36)
[build-system]
requires = ["hatchling", "hatch-vcs"]
build-backend = "hatchling.build"

[project]
name = "tabpfn_time_series"
dynamic = ["version"]

# ... later in file ...

[tool.hatch.version]
source = "vcs"
```

---

## Solution

**Implementation Time:** 2026-02-06 16:20

### Approach

Replaced dynamic VCS-based versioning with a static version number. This removes the dependency on git tags and allows the package to build regardless of its git context.

**Why This Solution:**

- Simple and reliable fix
- No need to restructure git repositories
- The version number (1.0.9) matches what was previously detected from git

### Code Changes

**Files Modified:**

1. `tabpfn-time-series/pyproject.toml` — Changed from dynamic to static version

**Before:**

```toml
[build-system]
requires = ["hatchling", "hatch-vcs"]
build-backend = "hatchling.build"

[project]
name = "tabpfn_time_series"
dynamic = ["version"]
# ...

[tool.hatch.version]
source = "vcs"
```

**After:**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "tabpfn_time_series"
version = "1.0.9"
# ...

# [tool.hatch.version] section removed
```

### Validation

**Verification Method:**

Ran `uv pip install -e tabpfn-time-series/` from parent directory.

**Test Results:**

```
Resolved 143 packages in 710ms
Built tabpfn-time-series @ file:///Users/Bourtguize-Ramel/Desktop/bobbee/analysis-forecasting/TabPFNApproach/tabpfn-time-series
Installed 94 packages in 1.42s
+ tabpfn-time-series==1.0.9 (from file:///...)
```

Package installed successfully with version 1.0.9.

---

## Follow-up Actions

None required. The fix is complete and verified.
