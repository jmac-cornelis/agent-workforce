##########################################################################################
#
# Module: shannon/outgoing_webhook.py
#
# Description: Helpers for Microsoft Teams Outgoing Webhook authentication
#              and response handling.
#
# Author: Cornelis Networks
#
##########################################################################################

from __future__ import annotations

import base64
import hashlib
import hmac
from typing import Optional


def extract_hmac_signature(authorization_header: Optional[str]) -> str:
    '''
    Extract the base64-encoded HMAC signature from a Teams Authorization header.
    '''
    raw = str(authorization_header or '').strip()
    if not raw:
        return ''

    parts = raw.split(None, 1)
    if len(parts) != 2:
        return ''

    scheme, signature = parts
    if scheme.lower() != 'hmac':
        return ''

    return signature.strip()


def compute_hmac_signature(secret: str, body_bytes: bytes) -> str:
    '''
    Compute the Teams Outgoing Webhook HMAC-SHA256 signature for *body_bytes*.
    '''
    key_bytes = base64.b64decode(str(secret or '').strip())
    digest = hmac.new(key_bytes, body_bytes, hashlib.sha256).digest()
    return base64.b64encode(digest).decode('utf-8')


def verify_hmac_signature(
    authorization_header: Optional[str],
    secret: str,
    body_bytes: bytes,
) -> bool:
    '''
    Verify a Teams Outgoing Webhook request signature.
    '''
    provided = extract_hmac_signature(authorization_header)
    if not provided or not str(secret or '').strip():
        return False

    calculated = compute_hmac_signature(secret, body_bytes)
    return hmac.compare_digest(provided, calculated)
