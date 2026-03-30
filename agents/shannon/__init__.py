##########################################################################################
#
# Module: agents/workforce/shannon/__init__.py
#
# Description: Shannon Communications agent package.
#
# Author: Cornelis Networks
#
##########################################################################################

from agents.shannon.agent import ShannonAgent
from agents.shannon.graph_client import TeamsGraphClient, GraphAPIError
from agents.shannon.registry import ChannelRegistry, ChannelMapping
from agents.shannon import cards

__all__ = [
    'ShannonAgent',
    'TeamsGraphClient',
    'GraphAPIError',
    'ChannelRegistry',
    'ChannelMapping',
    'cards',
]
