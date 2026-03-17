##########################################################################################
#
# Module: agents/workforce/shannon/__init__.py
#
# Description: Shannon Communications agent package.
#
# Author: Cornelis Networks
#
##########################################################################################

from agents.workforce.shannon.agent import ShannonAgent
from agents.workforce.shannon.graph_client import TeamsGraphClient, GraphAPIError
from agents.workforce.shannon.registry import ChannelRegistry, ChannelMapping
from agents.workforce.shannon import cards

__all__ = [
    'ShannonAgent',
    'TeamsGraphClient',
    'GraphAPIError',
    'ChannelRegistry',
    'ChannelMapping',
    'cards',
]
