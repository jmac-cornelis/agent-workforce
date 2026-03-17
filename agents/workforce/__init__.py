##########################################################################################
#
# Module: agents/workforce/__init__.py
#
# Description: Execution Spine workforce agents package.
#              Provides organized access to all Execution Spine agents.
#
# Author: Cornelis Networks
#
##########################################################################################

from agents.workforce.josephine.agent import JosephineAgent
from agents.workforce.ada.agent import AdaAgent
from agents.workforce.curie.agent import CurieAgent
from agents.workforce.faraday.agent import FaradayAgent
from agents.workforce.tesla.agent import TeslaAgent
from agents.workforce.hedy.agent import HedyAgent
from agents.workforce.linus.agent import LinusAgent

__all__ = [
    'JosephineAgent',
    'AdaAgent',
    'CurieAgent',
    'FaradayAgent',
    'TeslaAgent',
    'HedyAgent',
    'LinusAgent',
]
