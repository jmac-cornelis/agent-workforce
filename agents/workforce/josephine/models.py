##########################################################################################
#
# Module: agents/workforce/josephine/models.py
#
# Description: Data models for the Josephine Build & Package Agent.
#              Defines build requests, results, records, and failure
#              classification for the build execution pipeline.
#
# Author: Cornelis Networks
#
##########################################################################################

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class PublishMode(str, Enum):
    '''Build artifact publish mode.'''
    NONE = 'none'
    ADD = 'add'
    UPDATE = 'update'


class BuildStatus(str, Enum):
    '''Build job lifecycle status.'''
    SUBMITTED = 'submitted'
    QUEUED = 'queued'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'


class BuildRequest(BaseModel):
    '''
    Normalized build job request submitted to Josephine.

    Maps to POST /v1/build-jobs request body.
    '''
    repo_url: str
    git_ref: str
    build_map_path: str
    targets: List[str] = Field(default_factory=list)
    packages: List[str] = Field(default_factory=list)
    publish_mode: PublishMode = PublishMode.NONE
    workspace_profile_ref: Optional[str] = None
    variables: Dict[str, str] = Field(default_factory=dict)
    labels: Dict[str, str] = Field(default_factory=dict)


class BuildResult(BaseModel):
    '''
    Result of a completed build job.

    Contains the FuzeID, produced packages, metadata references,
    and log location.
    '''
    status: BuildStatus
    fuze_id: Optional[str] = None
    packages: List[str] = Field(default_factory=list)
    metadata_record_keys: List[str] = Field(default_factory=list)
    logs_ref: Optional[str] = None


class FailureResult(BaseModel):
    '''
    Machine-readable failure classification for a build job.

    Distinguishes retryable transient failures from deterministic
    build errors.
    '''
    code: str
    stage: str
    message: str
    retryable: bool = False


class BuildRecord(BaseModel):
    '''
    Durable record of a build job through its full lifecycle.

    Ties together the request, result, failure details, and timing.
    '''
    job_id: str
    status: BuildStatus = BuildStatus.SUBMITTED
    submitted_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    request: Optional[BuildRequest] = None
    result: Optional[BuildResult] = None
    failure: Optional[FailureResult] = None
    worker_id: Optional[str] = None
    correlation_id: Optional[str] = None
