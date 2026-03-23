##########################################################################################
#
# Module: shannon/app.py
#
# Description: FastAPI application for the Shannon Teams bot service.
#
# Author: Cornelis Networks
#
##########################################################################################

from __future__ import annotations

import logging
import os
import sys
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel, Field

from shannon.outgoing_webhook import verify_hmac_signature
from shannon.service import ShannonService

# Logging config - follows jira_utils.py pattern
log = logging.getLogger(os.path.basename(sys.argv[0]))


class NotificationRequest(BaseModel):
    agent_id: Optional[str] = None
    channel_id: Optional[str] = None
    title: str
    text: str
    body_lines: List[str] = Field(default_factory=list)


def create_app(service: Optional[ShannonService] = None) -> FastAPI:
    '''
    Create the Shannon FastAPI application.
    '''
    shannon_service = service or ShannonService()

    app = FastAPI(
        title='Shannon Teams Bot Service',
        version='0.1.0',
        description='Minimal-permission Teams bot service for the Cornelis agent workforce.',
    )
    app.state.shannon_service = shannon_service

    @app.get('/v1/bot/health')
    def bot_health() -> Dict[str, Any]:
        return shannon_service.get_health()

    @app.get('/v1/status/stats')
    def status_stats() -> Dict[str, Any]:
        return shannon_service.get_stats()

    @app.get('/v1/status/load')
    def status_load() -> Dict[str, Any]:
        return shannon_service.get_load()

    @app.get('/v1/status/work-summary')
    def status_work_summary() -> Dict[str, Any]:
        return shannon_service.get_work_summary()

    @app.get('/v1/status/tokens')
    def status_tokens() -> Dict[str, Any]:
        return shannon_service.get_token_status()

    @app.get('/v1/status/decisions')
    def status_decisions(limit: int = 10) -> List[Dict[str, Any]]:
        return shannon_service.get_decisions(limit=limit)

    @app.get('/v1/status/decisions/{record_id}')
    def status_decision(record_id: str) -> Dict[str, Any]:
        record = shannon_service.get_decision(record_id)
        if record is None:
            raise HTTPException(status_code=404, detail='Decision not found')
        return record

    @app.get('/v1/shannon/registry')
    def shannon_registry() -> Dict[str, Any]:
        return shannon_service.registry.to_dict()

    @app.post('/v1/bot/notify')
    def bot_notify(request: NotificationRequest) -> Dict[str, Any]:
        try:
            return shannon_service.post_notification(
                agent_id=request.agent_id,
                channel_id=request.channel_id,
                title=request.title,
                text=request.text,
                body_lines=request.body_lines,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post('/api/messages')
    def bot_messages(activity: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return shannon_service.process_teams_activity(activity)
        except Exception as exc:
            log.exception('Failed to process Teams activity')
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.post('/v1/teams/activities')
    def teams_activities(activity: Dict[str, Any]) -> Dict[str, Any]:
        return bot_messages(activity)

    @app.post('/v1/teams/outgoing-webhook')
    async def teams_outgoing_webhook(
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ) -> Dict[str, Any]:
        secret = str(os.getenv('SHANNON_TEAMS_OUTGOING_WEBHOOK_SECRET') or '').strip()
        body_bytes = await request.body()

        if not verify_hmac_signature(authorization, secret, body_bytes):
            raise HTTPException(status_code=401, detail='Invalid outgoing webhook signature')

        try:
            activity = await request.json()
        except Exception as exc:
            raise HTTPException(status_code=400, detail='Invalid JSON payload') from exc

        try:
            return shannon_service.process_outgoing_webhook_activity(activity)
        except Exception as exc:
            log.exception('Failed to process Teams outgoing webhook activity')
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    return app


app = create_app()


def run() -> None:
    import uvicorn

    host = os.getenv('SHANNON_HOST', '0.0.0.0')
    port = int(os.getenv('SHANNON_PORT', '8200'))
    uvicorn.run('shannon.app:app', host=host, port=port, reload=False)
