##########################################################################################
#
# Module: agents/workforce/faraday/models.py
#
# Description: Data models for the Faraday Test Executor Agent.
#              Defines test run requests, execution records, failure records,
#              and environment reservation references.
#
# Author: Cornelis Networks
#
##########################################################################################

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ExecutionStage(str, Enum):
    ACCEPTED = 'accepted'
    WAITING_FOR_ENVIRONMENT = 'waiting_for_environment'
    ENVIRONMENT_RESERVED = 'environment_reserved'
    STAGING_RUNTIME = 'staging_runtime'
    INVOKING_FUZE_TEST = 'invoking_fuze_test'
    RUNNING = 'running'
    COLLECTING_RESULTS = 'collecting_results'
    PUBLISHING_RESULTS = 'publishing_results'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'


class FailureClass(str, Enum):
    BAD_REQUEST = 'bad_request'
    MISSING_ARTIFACTS = 'missing_artifacts'
    RESERVATION_FAILURE = 'reservation_failure'
    ATF_CONFIG_FAILURE = 'atf_config_failure'
    PTA_FAILURE = 'pta_failure'
    DUT_FAILURE = 'dut_failure'
    TIMEOUT = 'timeout'
    INFRASTRUCTURE_LOSS = 'infrastructure_loss'


class TestRunRequest(BaseModel):
    '''Normalized test run submission request.'''
    build_id: str
    test_plan_id: str
    module: str
    project: str
    module_version: Optional[str] = None
    runtype: Optional[str] = None
    location: Optional[str] = None
    test_setup: Optional[str] = None
    suite_list: List[str] = Field(default_factory=list)
    runtime_overlays: List[str] = Field(default_factory=list)
    dut_filters: Optional[Dict[str, List[str]]] = None
    environment_reservation_ref: Optional[str] = None
    result_publication_policy: str = 'standard'


class EnvironmentReservation(BaseModel):
    '''Reference to a Tesla environment reservation for this test run.'''
    reservation_id: str
    environment_id: str
    location: str
    environment_class: str = 'mock'
    lease_expires_at: Optional[datetime] = None


class TestFailureRecord(BaseModel):
    '''Machine-readable failure classification for a test run.'''
    failure_class: FailureClass
    stage: ExecutionStage
    message: str
    retryable: bool = False
    details: Optional[Dict[str, Any]] = None


class TestExecutionRecord(BaseModel):
    '''
    Durable record of a test execution through its full lifecycle.

    Links build, plan, environment, and results into a single
    queryable record.
    '''
    test_run_id: str
    build_id: str
    test_plan_id: str
    stage: ExecutionStage = ExecutionStage.ACCEPTED
    worker_id: Optional[str] = None
    reservation: Optional[EnvironmentReservation] = None
    request: Optional[TestRunRequest] = None
    failure: Optional[TestFailureRecord] = None
    result_summary: Optional[Dict[str, Any]] = None
    artifact_refs: List[str] = Field(default_factory=list)
    submitted_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    correlation_id: Optional[str] = None
