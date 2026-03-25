##########################################################################################
#
# Module: notifications/base.py
#
# Description: Base notification interface for PM agent comment backends.
#
# Author: Cornelis Networks
#
##########################################################################################

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class NotificationBackend(ABC):
    @abstractmethod
    def send(
        self,
        ticket_key: str,
        message: str,
        level: str = 'flag',
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        raise NotImplementedError
