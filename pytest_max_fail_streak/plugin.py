"""Stop the run after N consecutive failing tests: ``--maxfail-streak=N``.

Unlike pytest's ``--maxfail``, which counts failures in total, this counts them in a row: a burst of consecutive
failures usually means the environment is down (a device is unreachable, a service doesn't respond), and every
remaining test would fail for the same reason.

Each test is judged once, after its teardown:
- it failed in any phase (setup, call or teardown)  -> the streak grows
- it passed                                         -> the streak resets
- it was skipped or xfailed                         -> neutral, the streak is unchanged

When the streak reaches N the run stops after the current test, the same way ``--maxfail`` stops it.
"""

import argparse

import pytest

FLAG = "--maxfail-streak"
TRACKER_PLUGIN_NAME = "max-fail-streak-tracker"

_FAILED = "failed"
_PASSED = "passed"


def positive_int(value: str) -> int:
    try:
        number = int(value)
    except ValueError as e:
        raise argparse.ArgumentTypeError(f"must be a positive integer, got {value!r}") from e
    if number < 1:
        raise argparse.ArgumentTypeError(f"must be a positive integer, got {value!r}")
    return number


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        FLAG,
        action="store",
        type=positive_int,
        default=None,
        metavar="N",
        help="Stop the run after N consecutive failing tests. Setup and teardown errors count as failures; "
        "skipped and xfailed tests don't break the streak. For a limit on failures in total, use --maxfail.",
    )


def pytest_configure(config: pytest.Config) -> None:
    if (limit := config.getoption(FLAG)) is None:
        return
    config.pluginmanager.register(FailStreakTracker(limit=limit), TRACKER_PLUGIN_NAME)


class FailStreakTracker:
    """Registered only when ``--maxfail-streak`` is set.

    A new tracker is created for every run and holds all of its state, so nothing leaks from one run to the next
    (e.g. several pytest runs in the same process).
    """

    def __init__(self, limit: int) -> None:
        self.limit = limit
        self.streak = 0
        self._session: pytest.Session | None = None
        self._outcomes: dict[str, str] = {}

    def pytest_sessionstart(self, session: pytest.Session) -> None:
        self._session = session

    def pytest_runtest_logreport(self, report: pytest.TestReport) -> None:
        if report.failed:
            self._outcomes[report.nodeid] = _FAILED
        elif report.when == "call" and report.passed:
            self._outcomes.setdefault(report.nodeid, _PASSED)

        if report.when != "teardown":
            return

        outcome = self._outcomes.pop(report.nodeid, None)
        if outcome == _FAILED:
            self.streak += 1
        elif outcome == _PASSED:
            self.streak = 0
        else:
            return  # skipped / xfailed: neutral

        if self.streak >= self.limit and self._session is not None:
            self._session.shouldfail = f"stopping after {self.limit} consecutive failures ({FLAG}={self.limit})"
