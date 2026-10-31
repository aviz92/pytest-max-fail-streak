![PyPI version](https://img.shields.io/pypi/v/pytest-max-fail-streak)
![Python](https://img.shields.io/badge/python->=3.12-blue)
![Development Status](https://img.shields.io/badge/status-stable-green)
![Maintenance](https://img.shields.io/maintenance/yes/2026)
![PyPI](https://img.shields.io/pypi/dm/pytest-max-fail-streak)
![License](https://img.shields.io/pypi/l/pytest-max-fail-streak)

---

# 💡 pytest-max-fail-streak
A pytest plugin that stops the run after **N consecutive** failing tests.

A burst of consecutive failures usually means the environment is down — a device is unreachable, a service doesn't respond — and every remaining test would fail for the same reason. Instead of waiting for all of them, stop early and get a clear signal.

---

## 📦 Installation
```bash
uv add pytest-max-fail-streak
```

---

## 🚀 Features
  - ✅ **Consecutive, not total** — complements pytest's `--maxfail`, which counts failures in total
  - ✅ **Catches a broken environment** — setup and teardown errors count, so an unreachable device stops the run
  - ✅ **A real stop** — the run ends like `--maxfail` ends it; remaining tests aren't run or reported as skipped
  - ✅ **Fair counting** — skipped and xfailed tests are neutral, and each test counts once
  - ✅ **Zero footprint without the flag** — nothing is registered, no hook runs

---

## 🛠️ How to Use
```bash
pytest --maxfail-streak=5
```
The run stops after 5 failing tests in a row, with exit code `1` and a summary line:
```
!!!!!!!!!! stopping after 5 consecutive failures (--maxfail-streak=5) !!!!!!!!!!
```

---

## ⚙️ How the Streak Is Counted
Each test is judged once, after its teardown:

| Test result | Effect on the streak |
|---|---|
| Failed in setup, call or teardown (failure or error) | +1 |
| Passed | Reset to 0 |
| Skipped or xfailed | Unchanged |

When the streak reaches `N`, the run stops after the current test.

`N` must be a positive integer; any other value is a usage error (exit code 4).

---

## 🤔 `--maxfail-streak` vs. `--maxfail`
| | `--maxfail=N` | `--maxfail-streak=N` |
|---|---|---|
| Counts | Failures in total | Failures in a row |
| Typical signal | "Too much is broken" | "The environment is down" |
| A passing test in between | Doesn't matter | Resets the count |

Both can be used together; whichever is reached first stops the run.

---

## ▶️ Usage Examples
### Enable in `pytest.ini` for CI
```ini
[pytest]
addopts =
    --maxfail-streak=5
```

---

## ⚠️ Notes
- With `pytest-xdist`, results arrive from several workers interleaved, so "consecutive" follows the order they arrive in, not the order of the test files.

---

## 🔁 Migrating from pytest-plugins
This plugin was previously `max_fail_streak` in `pytest-plugins`. Both register the `--maxfail-streak` option,
so don't install them together until you're on a `pytest-plugins` release without it.
Changes when migrating:
- The run now stops instead of skipping the remaining tests.
- Setup and teardown errors now count; skipped tests no longer reset the streak.

---

## 🤝 Contributing
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-addition`
3. Make your changes
4. Commit your changes: `git commit -m 'Add my addition'`
5. Push to the branch: `git push origin feature/my-addition`
6. Open a Pull Request

Additions that promote clean, productive, and maintainable development are always welcome.

---

## 📄 License
MIT License — see [LICENSE](LICENSE) for details.

---

## 🙏 Thanks
Thanks for exploring this repository! <br>
Happy coding!

[![GitHub](https://img.shields.io/badge/GitHub-aviz92-181717?logo=github)](https://github.com/aviz92)
&nbsp; [![PyPI](https://img.shields.io/badge/PyPI-aviz-3775A9?logo=pypi)](https://pypi.org/user/aviz/)
&nbsp; [![Blog](https://img.shields.io/badge/Blog-aviz92.github.io-0066CC?logo=googlechrome)](https://aviz92.github.io/)
&nbsp; [![LinkedIn](https://img.shields.io/badge/LinkedIn-avi--zaguri-0A66C2?logo=linkedin)](https://www.linkedin.com/in/avi-zaguri-41869b11b)
