##########################################################################################
#
# Module: tools/hypatia_tools.py
#
# Description: Hypatia documentation tools for agent use.
#              Wraps the Hypatia documentation workflow as agent-callable tools.
#
# Author: Cornelis Networks
#
##########################################################################################

import logging
import os
import sys
from typing import Optional

from tools.base import BaseTool, ToolResult, tool

# Logging config - follows jira_utils.py pattern
log = logging.getLogger(os.path.basename(sys.argv[0]))


@tool(
    description='Generate a Hypatia documentation record and review session'
)
def generate_hypatia_documentation(
    title: str,
    doc_type: str = 'engineering_reference',
    project_key: str = '',
    summary: str = '',
    source_paths: Optional[list[str]] = None,
    source_refs: Optional[list[str]] = None,
    evidence_paths: Optional[list[str]] = None,
    target_file: Optional[str] = None,
    confluence_title: Optional[str] = None,
    confluence_page: Optional[str] = None,
    confluence_space: Optional[str] = None,
    confluence_parent_id: Optional[str] = None,
    version_message: Optional[str] = None,
    validation_profile: str = 'default',
    persist: bool = True,
) -> ToolResult:
    '''
    Generate a Hypatia documentation record and review session.
    '''
    log.debug(
        f'generate_hypatia_documentation(title={title}, doc_type={doc_type}, '
        f'project_key={project_key}, target_file={target_file}, '
        f'confluence_title={confluence_title}, confluence_page={confluence_page}, '
        f'validation_profile={validation_profile}, persist={persist})'
    )

    try:
        from agents.hypatia.agent import HypatiaDocumentationAgent
        from agents.hypatia.models import DocumentationRequest
        from agents.hypatia.state.record_store import HypatiaRecordStore

        agent = HypatiaDocumentationAgent(project_key=project_key or None)
        request = DocumentationRequest(
            title=title,
            doc_type=doc_type,
            project_key=project_key,
            summary=summary,
            source_paths=list(source_paths or []),
            source_refs=list(source_refs or []),
            evidence_paths=list(evidence_paths or []),
            target_file=target_file,
            confluence_title=confluence_title,
            confluence_page=confluence_page,
            confluence_space=confluence_space,
            confluence_parent_id=confluence_parent_id,
            version_message=version_message,
            validation_profile=validation_profile,
        )
        record, review_session = agent.plan_documentation(request)

        result = {
            'record': record.to_dict(),
            'review_session': review_session.to_dict(),
        }

        if persist:
            stored = HypatiaRecordStore().save_record(
                record,
                summary_markdown=record.summary_markdown,
            )
            result['stored'] = stored

        return ToolResult.success(
            result,
            doc_id=record.doc_id,
            project_key=project_key,
            persisted=persist,
        )
    except Exception as e:
        log.error(f'Failed to generate Hypatia documentation: {e}')
        return ToolResult.failure(f'Failed to generate Hypatia documentation: {e}')


@tool(
    description='Get a persisted Hypatia documentation record by document ID'
)
def get_hypatia_record(
    doc_id: str,
) -> ToolResult:
    '''
    Get a persisted Hypatia documentation record by document ID.
    '''
    log.debug(f'get_hypatia_record(doc_id={doc_id})')

    try:
        from agents.hypatia.state.record_store import HypatiaRecordStore

        record = HypatiaRecordStore().get_record(doc_id)
        if not record:
            return ToolResult.failure(f'Hypatia record {doc_id} not found')

        return ToolResult.success(record, doc_id=doc_id)
    except Exception as e:
        log.error(f'Failed to get Hypatia record: {e}')
        return ToolResult.failure(f'Failed to get Hypatia record: {e}')


@tool(
    description='List persisted Hypatia documentation records'
)
def list_hypatia_records(
    doc_type: Optional[str] = None,
    limit: int = 20,
) -> ToolResult:
    '''
    List persisted Hypatia documentation records.
    '''
    log.debug(f'list_hypatia_records(doc_type={doc_type}, limit={limit})')

    try:
        from agents.hypatia.state.record_store import HypatiaRecordStore

        rows = HypatiaRecordStore().list_records(doc_type=doc_type, limit=limit)
        return ToolResult.success(rows, count=len(rows), doc_type=doc_type)
    except Exception as e:
        log.error(f'Failed to list Hypatia records: {e}')
        return ToolResult.failure(f'Failed to list Hypatia records: {e}')


class HypatiaTools(BaseTool):
    '''
    Collection of Hypatia documentation tools for agent use.
    '''

    @tool(description='Generate a Hypatia documentation record and review session')
    def generate_hypatia_documentation(
        self,
        title: str,
        doc_type: str = 'engineering_reference',
        project_key: str = '',
        summary: str = '',
        source_paths: Optional[list[str]] = None,
        source_refs: Optional[list[str]] = None,
        evidence_paths: Optional[list[str]] = None,
        target_file: Optional[str] = None,
        confluence_title: Optional[str] = None,
        confluence_page: Optional[str] = None,
        confluence_space: Optional[str] = None,
        confluence_parent_id: Optional[str] = None,
        version_message: Optional[str] = None,
        validation_profile: str = 'default',
        persist: bool = True,
    ) -> ToolResult:
        return generate_hypatia_documentation(
            title=title,
            doc_type=doc_type,
            project_key=project_key,
            summary=summary,
            source_paths=source_paths,
            source_refs=source_refs,
            evidence_paths=evidence_paths,
            target_file=target_file,
            confluence_title=confluence_title,
            confluence_page=confluence_page,
            confluence_space=confluence_space,
            confluence_parent_id=confluence_parent_id,
            version_message=version_message,
            validation_profile=validation_profile,
            persist=persist,
        )

    @tool(description='Get a persisted Hypatia documentation record by document ID')
    def get_hypatia_record(self, doc_id: str) -> ToolResult:
        return get_hypatia_record(doc_id)

    @tool(description='List persisted Hypatia documentation records')
    def list_hypatia_records(
        self,
        doc_type: Optional[str] = None,
        limit: int = 20,
    ) -> ToolResult:
        return list_hypatia_records(doc_type, limit)
