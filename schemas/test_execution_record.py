"""Canonical test execution records — shared across all agents."""

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TestRunRequest(BaseModel):
    """Request to execute a test suite against a build."""

    build_id: str = Field(..., description="Fuze build ID to test against")
    test_plan_id: str = Field(..., description="Test plan identifier (e.g. pr-fast-functional-v3)")
    test_level: str = Field(
        ...,
        description="Trigger class: pr | merge | nightly | release",
    )
    environment_id: str | None = Field(None, description="Target environment (e.g. hil-rack-03)")
    environment_mode: str = Field(
        "mock",
        description="Environment type: hardware_in_loop | mock | simulation",
    )
    config_overrides: dict[str, Any] = Field(default_factory=dict, description="Runtime config overrides")
    correlation_id: str = Field("", description="Cross-agent correlation identifier")
    requested_at: datetime = Field(default_factory=_utcnow)
    requested_by: str = Field("", description="Agent or user that requested the run")


class TestExecutionRecord(BaseModel):
    """Result of a completed test execution produced by Faraday."""

    test_run_id: str = Field(..., description="Unique test run identifier")
    build_id: str = Field(..., description="Fuze build ID tested")
    test_plan_id: str = Field(..., description="Test plan that was executed")
    test_level: str = Field(..., description="Trigger class: pr | merge | nightly | release")
    environment_id: str = Field(..., description="Environment where tests ran")
    environment_mode: str = Field(..., description="hardware_in_loop | mock | simulation")
    status: str = Field(
        ...,
        description="Execution outcome: passed | failed | error | cancelled | timeout",
    )
    total_tests: int = Field(0, description="Total number of test cases")
    passed_count: int = Field(0)
    failed_count: int = Field(0)
    skipped_count: int = Field(0)
    error_count: int = Field(0)
    started_at: datetime | None = None
    ended_at: datetime | None = None
    duration_seconds: float | None = None
    coverage_summary: dict[str, float] = Field(
        default_factory=dict,
        description="Coverage metrics (e.g. {unit: 82.1, functional: 64.4})",
    )
    log_uri: str | None = Field(None, description="URI to full test logs")
    artifact_uris: list[str] = Field(default_factory=list, description="URIs to test artifacts")
    failure_ids: list[str] = Field(
        default_factory=list,
        description="References to TestFailureRecord entries",
    )
    correlation_id: str = Field("")
    created_at: datetime = Field(default_factory=_utcnow)


class TestFailureRecord(BaseModel):
    """Individual test failure detail, linked from TestExecutionRecord."""

    failure_id: str = Field(..., description="Unique failure identifier")
    test_run_id: str = Field(..., description="Parent test run")
    test_case_id: str = Field(..., description="Fully qualified test case name")
    failure_type: str = Field(
        ...,
        description="Classification: assertion | crash | timeout | infrastructure | unknown",
    )
    message: str = Field("", description="Failure message or assertion text")
    stack_trace: str | None = None
    log_snippet: str | None = None
    is_known_flake: bool = Field(False, description="Whether this matches a known flaky pattern")
    jira_key: str | None = Field(None, description="Linked Jira issue if triaged")
    created_at: datetime = Field(default_factory=_utcnow)
