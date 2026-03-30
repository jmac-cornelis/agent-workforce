##########################################################################################
#
# Module: agents/workforce/tesla/models.py
#
# Description: Data models for the Tesla Environment Manager Agent.
#              Defines environments, reservations, reservation requests,
#              and health status records.
#
# Author: Cornelis Networks
#
##########################################################################################

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class EnvironmentClass(str, Enum):
    MOCK = 'mock'
    HIL = 'hil'


class EnvironmentStatus(str, Enum):
    AVAILABLE = 'available'
    RESERVED = 'reserved'
    MAINTENANCE = 'maintenance'
    QUARANTINED = 'quarantined'
    DEGRADED = 'degraded'
    OFFLINE = 'offline'


class ReservationStatus(str, Enum):
    GRANTED = 'granted'
    QUEUED = 'queued'
    REJECTED_NO_CAPACITY = 'rejected_no_capacity'
    REJECTED_CAPABILITY_MISMATCH = 'rejected_capability_mismatch'
    REJECTED_POLICY = 'rejected_policy'
    EXPIRED = 'expired'
    RELEASED = 'released'


class Environment(BaseModel):
    '''A reservable test environment with capabilities and status.'''
    environment_id: str
    location: str
    environment_class: EnvironmentClass = EnvironmentClass.MOCK
    hardware_profile: Optional[str] = None
    topology_profile: Optional[str] = None
    dut_set: List[str] = Field(default_factory=list)
    capabilities: List[str] = Field(default_factory=list)
    status: EnvironmentStatus = EnvironmentStatus.AVAILABLE


class ReservationRequest(BaseModel):
    '''Request to reserve a test environment.'''
    hardware_profile: Optional[str] = None
    topology_profile: Optional[str] = None
    environment_class: EnvironmentClass = EnvironmentClass.MOCK
    duration_seconds: int = 3600
    test_plan_id: Optional[str] = None
    location_preference: Optional[str] = None
    dut_filters: Optional[Dict[str, List[str]]] = None


class Reservation(BaseModel):
    '''An active or completed environment reservation.'''
    reservation_id: str
    environment_id: str
    status: ReservationStatus = ReservationStatus.GRANTED
    location: str = ''
    environment_class: EnvironmentClass = EnvironmentClass.MOCK
    lease_ttl_seconds: int = 3600
    granted_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    released_at: Optional[datetime] = None
    test_plan_id: Optional[str] = None
    correlation_id: Optional[str] = None


class HealthStatus(BaseModel):
    '''Health and availability record for an environment.'''
    environment_id: str
    reachable: bool = True
    dut_reachable: bool = True
    pta_ready: bool = True
    last_check_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    recent_failures: int = 0
    notes: Optional[str] = None
