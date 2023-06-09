from datetime import datetime, timezone
from typing import Dict, List, Set

from flask import request
from pydantic import BaseModel, Field

import asyncio 

import sys

from globus_action_provider_tools import (
    ActionProviderDescription,
    ActionRequest,
    ActionStatus,
    ActionStatusValue,
    AuthState,
)
from globus_action_provider_tools.authorization import (
    authorize_action_access_or_404,
    authorize_action_management_or_404,
)
from globus_action_provider_tools.flask import ActionProviderBlueprint
from globus_action_provider_tools.flask.exceptions import ActionConflict, ActionNotFound
from globus_action_provider_tools.flask.types import (
    ActionCallbackReturn,
    ActionLogReturn,
)

from backend import action_database, request_database

class ActionProviderInput(BaseModel):
    prefix: str = Field(
        ..., title="Selected segment to process", description="Segement to process, E.G 'CC-MAIN-2017-09'"
    )
    chunk_size: int = Field(
        ..., title="Chunk size", description="Number of URI's to process at a time"
    )

    class Config:
        schema_extra = {"example": {
            "prefix": "CC-MAIN-2017-09",
            "chunk_size": 2
            }}

# Modified globus_auth_scope to be the newly generated scope
# https://auth.globus.org/scopes/27c72d0c-9a46-4a5d-a6a5-bd2cd35bc574/action_all
description = ActionProviderDescription(
    globus_auth_scope="https://auth.globus.org/scopes/27c72d0c-9a46-4a5d-a6a5-bd2cd35bc574/action_all",
    title="Common Crawl pre-processing",
    admin_contact="ael56@uclive.ac.nz",
    synchronous=True,
    input_schema=ActionProviderInput,
    api_version="1.0",
    subtitle="Get suitable subtitle from Jonathan",
    description="Get suitable description from Jonathan",
    keywords=["Common Crawl", "NLP", "productivity"],
    visible_to=["public"],
    runnable_by=["all_authenticated_users"],
    administered_by=["ael56@uclive.ac.nz"],
)

aptb = ActionProviderBlueprint(
    name="cc",
    import_name=__name__,
    url_prefix="/cc",
    provider_description=description
)

@aptb.action_enumerate
def action_enumeration(auth: AuthState, params: Dict[str, Set]) -> List[ActionStatus]:
    """
    This is an optional endpoint, useful for allowing requestors to enumerate
    actions filtered by ActionStatus and role.

    The params argument will always be a dict containing the incoming request's
    validated query arguments. There will be two keys, 'statuses' and 'roles',
    where each maps to a set containing the filter values for the key. A typical
    params object will look like:

        {
            "statuses": {<ActionStatusValue.ACTIVE: 3>},
            "roles": {"creator_id"}
        }

    Notice that the value for the "statuses" key is an Enum value.
    """
    statuses = params["statuses"]
    roles = params["roles"]
    matches = []

    for _, action in action_database.items():
        if action.status in statuses:
            # Create a set of identities that are allowed to access this action,
            # based on the roles being queried for
            allowed_set = set()
            for role in roles:
                identities = getattr(action, role)
                if isinstance(identities, str):
                    allowed_set.add(identities)
                else:
                    allowed_set.update(identities)

            # Determine if this request's auth allows access based on the
            # allowed_set
            authorized = auth.check_authorization(allowed_set)
            if authorized:
                matches.append(action)

    return matches

@aptb.action_run
def my_action_run(action_request: ActionRequest, auth: AuthState) -> ActionCallbackReturn:
    """
    Implement custom business logic related to instantiating an Action here.
    Once launched, collect details on the Action and create an ActionStatus
    which records information on the instantiated Action and gets stored.
    """
    
    # Regestration of action
    print('Action running', file=sys.stderr)
    print(f'Action request ID: {action_request.request_id}', file=sys.stderr)

    # Regester action request to parse out continuing requests

    # ID:urn:globus:auth:identity:25af9d3b-aeb8-4f44-9c88-3264ad82a3ae:flows_req_d869a4c4-ced1-4e25-a6b8-d6a0d6f7babc

    caller_id = auth.effective_identity
    prefix_to_process = action_request.body['prefix']
    full_request_id = f"{caller_id}:{prefix_to_process}"
    prev_request = request_database.get(full_request_id)

    print(f"FULL REQUEST ID:{full_request_id}")

    if prev_request is not None:
        """
        NOTE: This is needed because the Globus client sends multiple
        post requests to the server when starting an action (is this 
        for redundency?, traffic issues?). This stops further requests
        once a unique action is logged, and returns the status of the 
        currently logged request.
        """
        if prev_request[0] == request:
            return my_action_status(prev_request[1], auth)
        else:
            raise ActionConflict(
                f"Request with id {request_id} already present with different parameters"
            )
        
    action_status = ActionStatus(
        status=ActionStatusValue.ACTIVE,
        creator_id=str(auth.effective_identity),
        label=action_request.label or None,
        monitor_by=action_request.monitor_by or auth.identities,
        manage_by=action_request.manage_by or auth.identities,
        start_time=datetime.now(timezone.utc).isoformat(),
        completion_time=None,
        release_after=action_request.release_after or "P30D",
        display_status=ActionStatusValue.ACTIVE,
        details={},
    )
    # Update action_database with action object
    action_database[action_status.action_id] = action_status
    # update request_database with unique request ID
    request_database[full_request_id] = (request, action_status.action_id)

    CC_processing(action_status.action_id, action_request.body)
    # dummy_logic(action_status.action_id, action_request.body) # Testing logic

    return action_status

# TODO strongly define request_body 
def CC_processing(action_id: str, request_body):

    import glob

    # define file structure & get job_path 
    data_store = "data_store/"
    job_directory = request_body['prefix']
    job_path = f"{data_store}{job_directory}/jobs/{glob.glob(f'{data_store}{job_directory}/jobs/*')[0].split('/')[-1]}"

    # Create an instance of the custom CC corpus class
    print(request_body)
    from common_crawl_corpus.cc_corpus import CC_Corpus
    CC_Corpus = CC_Corpus()
    CC_Corpus.process_crawl(job_path,request_body['prefix'], chunk_size=request_body['chunk_size'])

    # Get the action from database
    action_status = action_database.get(action_id)
    action_status.completion_time=datetime.now(timezone.utc).isoformat()
    action_status.status=ActionStatusValue.SUCCEEDED
    action_status.display_status=ActionStatusValue.SUCCEEDED
    # action_status.completion_time=(end_processing-begin_processing)

    # Regester the edited action_status
    action_database[action_id] = action_status

# TODO strongly define request_body
def dummy_logic(action_id: str, request_body) -> ActionCallbackReturn:
    """
    Dummy logic that waits x amount of time, and then performs a callback 
    to simiulate an action completing.
    Logic is currently bocking. 
    """
    import time

    # time function to include in completion time field
    begin_processing = time.time()
    
    print(f"Full Action ID: {action_id}", file=sys.stderr)
    print(f"Passed action request body: {request_body}", file=sys.stderr)
    # Simulation of some action taking time
    time.sleep(60) 

    end_processing = time.time()

    # Get the action from database
    action_status = action_database.get(action_id)
    action_status.completion_time=datetime.now(timezone.utc).isoformat()
    action_status.status=ActionStatusValue.SUCCEEDED
    action_status.display_status=ActionStatusValue.SUCCEEDED
    action_status.completion_time=(end_processing-begin_processing)

    # Regester the edited action_status
    action_database[action_id] = action_status

    print(action_status)
    print(action_database[action_id])
    print("Action processing completed", file=sys.stderr)
    print("Subprocess terminating", file=sys.stderr)

    return action_status


@aptb.action_status
def my_action_status(action_id: str, auth: AuthState) -> ActionCallbackReturn:
    """
    Query for the action_id in some storage backend to return the up-to-date
    ActionStatus. It's possible that some ActionProviders will require querying
    an external system to get up to date information on an Action's status.
    """
    action_status = action_database.get(action_id)
    if action_status is None:
        raise ActionNotFound(f"No action with {action_id}")
    authorize_action_access_or_404(action_status, auth)
    return action_status


@aptb.action_cancel
def my_action_cancel(action_id: str, auth: AuthState) -> ActionCallbackReturn:
    """
    Only Actions that are not in a completed state may be cancelled.
    Cancellations do not necessarily require that an Action's execution be
    stopped. Once cancelled, the ActionStatus object should be updated and
    stored.
    """
    action_status = action_database.get(action_id)
    if action_status is None:
        raise ActionNotFound(f"No action with {action_id}")

    authorize_action_management_or_404(action_status, auth)
    if action_status.is_complete():
        raise ActionConflict("Cannot cancel complete action")

    action_status.status = ActionStatusValue.FAILED
    action_status.display_status = f"Cancelled by {auth.effective_identity}"
    action_database[action_id] = action_status
    return action_status


@aptb.action_release
def my_action_release(action_id: str, auth: AuthState) -> ActionCallbackReturn:
    """
    Only Actions that are in a completed state may be released. The release
    operation removes the ActionStatus object from the data store. The final, up
    to date ActionStatus is returned after a successful release.
    """
    action_status = action_database.get(action_id)
    if action_status is None:
        raise ActionNotFound(f"No action with {action_id}")

    authorize_action_management_or_404(action_status, auth)
    if not action_status.is_complete():
        raise ActionConflict("Cannot release incomplete Action")

    action_status.display_status = f"Released by {auth.effective_identity}"
    # TODO currently dont understand the release mechanic and this might break
    request_database.pop(action_id)
    action_database.pop(action_id)
    return action_status


@aptb.action_log
def my_action_log(action_id: str, auth: AuthState) -> ActionLogReturn:
    """
    Action Providers can optionally support a logging endpoint to return
    detailed information on an Action's execution history. Pagination and
    filters are supported as query parameters and can be used to control what
    details are returned to the requestor.
    """
    pagination = request.args.get("pagination")
    filters = request.args.get("filters")
    return ActionLogReturn(
        code=200,
        description=f"This is an example of a detailed log entry for {action_id}",
        **{
            "time": "TODAY",
            "details": {
                "action_id": "Transfer",
                "filters": filters,
                "pagination": pagination,
            },
        },
    )
