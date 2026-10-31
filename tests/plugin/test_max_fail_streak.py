import pytest

STOP_MESSAGE = "*stopping after {limit} consecutive failures (--maxfail-streak={limit})*"


class TestStopsOnStreak:
    def test_stops_after_streak_of_call_failures(self, pytester: pytest.Pytester) -> None:
        pytester.makepyfile(
            """
            def test_fail_1(): assert False
            def test_fail_2(): assert False
            def test_fail_3(): assert False
            def test_not_run(): assert True
        """
        )
        result = pytester.runpytest_subprocess("--maxfail-streak=3")
        assert result.ret == pytest.ExitCode.TESTS_FAILED, f"Expected TESTS_FAILED, got {result.ret}"
        result.assert_outcomes(failed=3)
        result.stdout.fnmatch_lines([STOP_MESSAGE.format(limit=3)])
        result.stdout.no_fnmatch_line("*test_not_run*")

    def test_remaining_tests_are_not_reported_as_skipped(self, pytester: pytest.Pytester) -> None:
        pytester.makepyfile(
            """
            def test_fail_1(): assert False
            def test_fail_2(): assert False
            def test_a(): assert True
            def test_b(): assert True
        """
        )
        result = pytester.runpytest_subprocess("--maxfail-streak=2")
        result.assert_outcomes(failed=2, skipped=0, passed=0)

    def test_streak_resets_after_passing_test(self, pytester: pytest.Pytester) -> None:
        pytester.makepyfile(
            """
            def test_fail_1(): assert False
            def test_fail_2(): assert False
            def test_pass(): assert True
            def test_fail_3(): assert False
            def test_fail_4(): assert False
            def test_fail_5(): assert False
            def test_not_run(): assert True
        """
        )
        result = pytester.runpytest_subprocess("--maxfail-streak=3")
        assert result.ret == pytest.ExitCode.TESTS_FAILED, f"Expected TESTS_FAILED, got {result.ret}"
        result.assert_outcomes(failed=5, passed=1)

    def test_streak_below_limit_runs_all_tests(self, pytester: pytest.Pytester) -> None:
        pytester.makepyfile(
            """
            def test_fail_1(): assert False
            def test_pass_1(): assert True
            def test_fail_2(): assert False
            def test_pass_2(): assert True
        """
        )
        result = pytester.runpytest_subprocess("--maxfail-streak=2")
        assert result.ret == pytest.ExitCode.TESTS_FAILED, f"Expected TESTS_FAILED, got {result.ret}"
        result.assert_outcomes(failed=2, passed=2)
        result.stdout.no_fnmatch_line("*stopping after*")

    def test_limit_of_one_stops_on_first_failure(self, pytester: pytest.Pytester) -> None:
        pytester.makepyfile(
            """
            def test_pass(): assert True
            def test_fail(): assert False
            def test_not_run(): assert True
        """
        )
        result = pytester.runpytest_subprocess("--maxfail-streak=1")
        result.assert_outcomes(passed=1, failed=1)


class TestWhatCountsAsFailure:
    def test_setup_errors_count(self, pytester: pytest.Pytester) -> None:
        # The main use case: the environment is down, so every test errors in setup.
        pytester.makepyfile(
            """
            import pytest

            @pytest.fixture
            def device():
                raise ConnectionError("device unreachable")

            def test_1(device): pass
            def test_2(device): pass
            def test_3(device): pass
            def test_4(device): pass
        """
        )
        result = pytester.runpytest_subprocess("--maxfail-streak=2")
        assert result.ret == pytest.ExitCode.TESTS_FAILED, f"Expected TESTS_FAILED, got {result.ret}"
        result.assert_outcomes(errors=2)
        result.stdout.fnmatch_lines([STOP_MESSAGE.format(limit=2)])

    def test_teardown_error_counts(self, pytester: pytest.Pytester) -> None:
        pytester.makepyfile(
            """
            import pytest

            @pytest.fixture
            def broken_cleanup():
                yield
                raise RuntimeError("cleanup failed")

            def test_1(broken_cleanup): pass
            def test_2(broken_cleanup): pass
            def test_not_run(): pass
        """
        )
        result = pytester.runpytest_subprocess("--maxfail-streak=2")
        result.assert_outcomes(passed=2, errors=2)
        result.stdout.no_fnmatch_line("*test_not_run PASSED*")
        result.stdout.fnmatch_lines([STOP_MESSAGE.format(limit=2)])

    def test_test_failing_in_call_and_teardown_counts_once(self, pytester: pytest.Pytester) -> None:
        pytester.makepyfile(
            """
            import pytest

            @pytest.fixture
            def broken_cleanup():
                yield
                raise RuntimeError("cleanup failed")

            def test_double_failure(broken_cleanup): assert False
            def test_still_runs(): assert True
        """
        )
        result = pytester.runpytest_subprocess("--maxfail-streak=2")
        result.assert_outcomes(failed=1, errors=1, passed=1)
        result.stdout.no_fnmatch_line("*stopping after*")

    def test_skipped_test_is_neutral(self, pytester: pytest.Pytester) -> None:
        pytester.makepyfile(
            """
            import pytest

            def test_fail_1(): assert False
            def test_skipped(): pytest.skip("not relevant here")
            def test_fail_2(): assert False
            def test_not_run(): assert True
        """
        )
        result = pytester.runpytest_subprocess("--maxfail-streak=2")
        result.assert_outcomes(failed=2, skipped=1)
        result.stdout.fnmatch_lines([STOP_MESSAGE.format(limit=2)])

    def test_xfailed_test_is_neutral(self, pytester: pytest.Pytester) -> None:
        pytester.makepyfile(
            """
            import pytest

            def test_fail_1(): assert False

            @pytest.mark.xfail(reason="known")
            def test_expected_failure(): assert False

            def test_fail_2(): assert False
            def test_not_run(): assert True
        """
        )
        result = pytester.runpytest_subprocess("--maxfail-streak=2")
        result.assert_outcomes(failed=2, xfailed=1)


class TestWithoutFlag:
    def test_without_flag_all_tests_run(self, pytester: pytest.Pytester) -> None:
        pytester.makepyfile(
            """
            def test_fail_1(): assert False
            def test_fail_2(): assert False
            def test_fail_3(): assert False
            def test_fail_4(): assert False
        """
        )
        result = pytester.runpytest_subprocess()
        result.assert_outcomes(failed=4)

    def test_tracker_not_registered_without_flag(self, pytester: pytest.Pytester) -> None:
        pytester.makeconftest(
            """
            def pytest_sessionstart(session):
                assert not session.config.pluginmanager.has_plugin("max-fail-streak-tracker")
        """
        )
        pytester.makepyfile("def test_ok():\n    assert True\n")
        result = pytester.runpytest_subprocess()
        assert result.ret == pytest.ExitCode.OK, f"Expected OK, got {result.ret}"

    def test_no_state_leaks_between_runs_in_same_process(self, pytester: pytest.Pytester) -> None:
        # Regression: the state used to live in a module-level dict, so a later run without the flag skipped tests.
        pytester.makepyfile(
            test_fails="""
            def test_f1(): assert False
            def test_f2(): assert False
            def test_f3(): assert False
        """,
            test_passes="""
            def test_p1(): assert True
            def test_p2(): assert True
        """,
        )
        first = pytester.runpytest_inprocess("test_fails.py", "--maxfail-streak=2")
        first.assert_outcomes(failed=2)
        second = pytester.runpytest_inprocess("test_passes.py")
        second.assert_outcomes(passed=2)


class TestInvalidValue:
    @pytest.mark.parametrize("value", ["abc", "0", "-1", "1.5"])
    def test_invalid_value_is_usage_error(self, pytester: pytest.Pytester, value: str) -> None:
        pytester.makepyfile("def test_ok():\n    assert True\n")
        result = pytester.runpytest_subprocess(f"--maxfail-streak={value}")
        assert result.ret == pytest.ExitCode.USAGE_ERROR, f"Expected USAGE_ERROR, got {result.ret}"
        result.stderr.fnmatch_lines([f"*--maxfail-streak*must be a positive integer, got '{value}'*"])

    def test_help_text(self, pytester: pytest.Pytester) -> None:
        result = pytester.runpytest_subprocess("--help")
        result.stdout.fnmatch_lines(["*--maxfail-streak=N*Stop the run after N consecutive failing tests*"])
        result.stdout.no_fnmatch_line("*Default is 3*")
