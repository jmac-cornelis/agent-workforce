##########################################################################################
#
# Module: tools/hemingway_tools.py
#
# Description: Hemingway documentation tools for agent use.
#              Wraps the Hemingway documentation workflow as agent-callable tools.
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
    description='Generate a Hemingway documentation record and review session'
)
def generate_hemingway_documentation(
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
    Generate a Hemingway documentation record and review session.
    '''
    log.debug(
        f'generate_hemingway_documentation(title={title}, doc_type={doc_type}, '
        f'project_key={project_key}, target_file={target_file}, '
        f'confluence_title={confluence_title}, confluence_page={confluence_page}, '
        f'validation_profile={validation_profile}, persist={persist})'
    )

    try:
        from agents.hemingway.agent import HemingwayDocumentationAgent
        from agents.hemingway.models import DocumentationRequest
        from agents.hemingway.state.record_store import HemingwayRecordStore

        agent = HemingwayDocumentationAgent(project_key=project_key or None)
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
            stored = HemingwayRecordStore().save_record(
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
        log.error(f'Failed to generate Hemingway documentation: {e}')
        return ToolResult.failure(f'Failed to generate Hemingway documentation: {e}')


@tool(
    description='Get a persisted Hemingway documentation record by document ID'
)
def get_hemingway_record(
    doc_id: str,
) -> ToolResult:
    '''
    Get a persisted Hemingway documentation record by document ID.
    '''
    log.debug(f'get_hemingway_record(doc_id={doc_id})')

    try:
        from agents.hemingway.state.record_store import HemingwayRecordStore

        record = HemingwayRecordStore().get_record(doc_id)
        if not record:
            return ToolResult.failure(f'Hemingway record {doc_id} not found')

        return ToolResult.success(record, doc_id=doc_id)
    except Exception as e:
        log.error(f'Failed to get Hemingway record: {e}')
        return ToolResult.failure(f'Failed to get Hemingway record: {e}')


@tool(
    description='List persisted Hemingway documentation records'
)
def list_hemingway_records(
    doc_type: Optional[str] = None,
    limit: int = 20,
) -> ToolResult:
    '''
    List persisted Hemingway documentation records.
    '''
    log.debug(f'list_hemingway_records(doc_type={doc_type}, limit={limit})')

    try:
        from agents.hemingway.state.record_store import HemingwayRecordStore

        rows = HemingwayRecordStore().list_records(doc_type=doc_type, limit=limit)
        return ToolResult.success(rows, count=len(rows), doc_type=doc_type)
    except Exception as e:
        log.error(f'Failed to list Hemingway records: {e}')
        return ToolResult.failure(f'Failed to list Hemingway records: {e}')


class HemingwayTools(BaseTool):
    '''
    Collection of Hemingway documentation tools for agent use.
    '''

    @tool(description='Generate a Hemingway documentation record and review session')
    def generate_hemingway_documentation(
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
        return generate_hemingway_documentation(
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

    @tool(description='Get a persisted Hemingway documentation record by document ID')
    def get_hemingway_record(self, doc_id: str) -> ToolResult:
        return get_hemingway_record(doc_id)

    @tool(description='List persisted Hemingway documentation records')
    def list_hemingway_records(
        self,
        doc_type: Optional[str] = None,
        limit: int = 20,
    ) -> ToolResult:
        return list_hemingway_records(doc_type, limit)


# Legacy compatibility aliases during the rename transition.
generate_hypatia_documentation = generate_hemingway_documentation
get_hypatia_record = get_hemingway_record
list_hypatia_records = list_hemingway_records
HypatiaTools = HemingwayTools
