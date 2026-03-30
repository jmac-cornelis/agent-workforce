##########################################################################################
#
# Module: agents
#
# Description: Agent definitions for Cornelis Agent Pipeline.
#              Provides specialized agents for release planning workflow.
#
# Author: Cornelis Networks
#
##########################################################################################

from agents.base import BaseAgent, AgentConfig, AgentResponse
from agents.drucker.agent import DruckerCoordinatorAgent
from agents.drucker.models import (
    DruckerAction,
    DruckerFinding,
    DruckerHygieneReport,
    DruckerRequest,
)
from agents.gantt.agent import GanttProjectPlannerAgent
from agents.gantt.components import (
    BacklogInterpreter,
    DependencyMapper,
    MilestonePlanner,
    PlanningSummarizer,
    RiskProjector,
)
from agents.hypatia.agent import HypatiaDocumentationAgent
from agents.hypatia.models import (
    DocumentationImpactRecord,
    DocumentationPatch,
    DocumentationRecord,
    DocumentationRequest,
    PublicationRecord,
)
from agents.orchestrator import ReleasePlanningOrchestrator
from agents.jira_analyst import JiraAnalystAgent
from agents.planning_agent import PlanningAgent
from agents.vision_analyzer import VisionAnalyzerAgent
from agents.review_agent import ReviewAgent

__all__ = [
    'BaseAgent',
    'AgentConfig',
    'AgentResponse',
    'DruckerAction',
    'DruckerCoordinatorAgent',
    'DruckerFinding',
    'DruckerHygieneReport',
    'DruckerRequest',
    'BacklogInterpreter',
    'DependencyMapper',
    'DocumentationImpactRecord',
    'DocumentationPatch',
    'DocumentationRecord',
    'DocumentationRequest',
    'GanttProjectPlannerAgent',
    'HypatiaDocumentationAgent',
    'ReleasePlanningOrchestrator',
    'JiraAnalystAgent',
    'MilestonePlanner',
    'PlanningAgent',
    'PlanningSummarizer',
    'PublicationRecord',
    'RiskProjector',
    'VisionAnalyzerAgent',
    'ReviewAgent',
]
