# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-10-31

First standalone release. Extracted from the `max_fail_streak` plugin of [pytest-plugins](https://github.com/aviz92/pytest-plugins).

### Changed
- The run **stops** when the streak is reached, the same way `--maxfail` stops it, instead of skipping every remaining test one by one. Remaining tests are not run and not reported.
- Setup and teardown errors count toward the streak (the main case: the environment is down and every test errors in setup).
- Skipped and xfailed tests are neutral: they no longer reset the streak.
- Each test counts once, even if it fails in both its call and its teardown.
- No dependency on the pytest-plugins report.

### Fixed
- State leaked between runs in the same process: a later run **without** the flag skipped passing tests.
- A negative value skipped every test, including passing ones.
- A non-numeric value crashed pytest with an internal error; `0` silently disabled the plugin. Any value that isn't a positive integer is now a usage error.
- The help text claimed a default of 3; there is no default, the plugin is off without the flag.

---
