import json
import keyring
import pandas as pd
import pythoncom
import re
import requests
import streamlit
import time
import urllib3
import win32com.client

# Suppress warning produced from opting to not verify certificate.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def sign_in(base_server_url: str, site_id: str, token_name: str, token_value: str, verify_certificate: bool = True) -> dict | bool:
    """
    Verifies the user has access to the Tableau Server or Tableau Cloud instance by attempting to sign-in.

    Args:
        base_server_url: The base URL portion of the full Tableau Server or Tableau Cloud instance URL input.
        site_id (str): The site ID value correspond the the Tableau Server or Tableau Cloud instance.
        token_name (str): The name of the personal access token configured.
        token_value (str): The secret value corresponding to the personal access token configured.
        verify_certificate (bool): Indicates whether the server's SSL/TLS certificate should be verified.
            By default, this option will be enabled to mitigate security risks. If the server contains a
            self-signed certificate, then this box can be unchecked.

    Returns:
        boolean: True if access verified, otherwise False.    
    """
    # Sign-in to Tableau Server or Tableau Cloud instance.
    sign_in_url = f'{base_server_url}/api/3.24/auth/signin'
    payload = {
        'credentials': {
            'personalAccessTokenName': token_name,
            'personalAccessTokenSecret': token_value,
            'site': {
                'contentUrl': site_id
            }
        }
    }
    headers = {
        'accept': 'application/json',
        'content-type': 'application/json'
    }
    sign_in_request = requests.post(sign_in_url, json=payload, headers=headers, verify=verify_certificate)
    
    if sign_in_request.status_code != 200:
        sign_in_exception = Exception(f'Sign-in failed with status code {sign_in_request.status_code}')
        streamlit.exception(sign_in_exception)
        return False

    # Convert response to dictionary to extract the token and site ID for the subsequent subscription request.
    sign_in_response = json.loads(sign_in_request.content)
    # Extract token and site ID.
    token = sign_in_response['credentials']['token']
    site_luid = sign_in_response['credentials']['site']['id']
    headers['X-tableau-auth'] = token
    headers['site_luid'] = site_luid
    return headers

def sign_out(base_server_url: str, headers: dict, verify_certificate: bool = True) -> None:
    """
    Signs the authenticated user out of the Tableau Server or Tableau Cloud instance.

    Args:
        base_server_url: The base URL portion of the full Tableau Server or Tableau Cloud instance URL input.
        headers (dict): The dictionary containing the header information for subsequent API requests.
            This also includes the site LUID for the request URLs.
        verify_certificate (bool): Indicates whether the server's SSL/TLS certificate should be verified.
            By default, this option will be enabled to mitigate security risks. If the server contains a
            self-signed certificate, then this box can be unchecked.
    Returns:
        None
    """
    sign_out_url = f'{base_server_url}/api/3.24/auth/signout'
    sign_out_request = requests.post(sign_out_url, headers=headers, verify=verify_certificate)
    return None

def extract_site_id(full_server_url: str) -> str | None:
    """
    Given a full server URL, returns the site ID.

    Args:
        full_server_url: The full server URL of the Tableau Server or Tableau Cloud instance.
    
    Returns:
        Site ID (str): The site ID portion of the full server URL.
    """
    match = re.search(r'/site/([^/#]+)', full_server_url)
    return match.group(1) if match else None

def extract_base_server_url(full_server_url: str) -> str | None:
    """
    Given a full server URL, returns the base URL.

    Args:
        full_server_url: The full server URL of the Tableau Server or Tableau Cloud instance.
    
    Returns:
        base url (str): The base URL portion of the full server URL input.
    """
    match = re.match(r'(https?://[^/]+)', full_server_url)
    return match.group(1) if match else None

def is_fetch_suspended_tasks_button_enabled() -> bool:
    """
    Ensures the user has provided values for all required input fields.

    Returns:
        bool: True if all required inputs are populated, False otherwise.
    """
    required_keys = [
        'FULL_SERVER_URL', 'BASE_SERVER_URL', 'INSTANCE_TYPE',
        'TOKEN_NAME', 'TOKEN_VALUE', 'TASK_FAILURE_LIMIT'
    ]
    return all(streamlit.session_state[key] for key in required_keys)

def is_send_email_reminder_button_enabled() -> bool:
    """
    Ensures the user has provided values for all required input fields.

    Returns:
        bool: True if all required inputs are populated, False otherwise.
    """
    required_keys = [
        'suspended_extract_refresh_tasks', 
        'suspended_flow_tasks',
        'suspended_subscription_tasks',
    ]
    return any(not streamlit.session_state[key] is None for key in required_keys)

def send_email(suspended_extract_refresh_tasks: pd.DataFrame, suspended_flow_tasks: pd.DataFrame, suspended_subscription_tasks: pd.DataFrame) -> None:
    """Sends an email reminder using the Outlook application and account configured on the local machine."""
    # Multi-threaded environment requires initializing the COM library for the current thread.
    pythoncom.CoInitialize()
    try:
        # Create an instance of Outlook
        outlook = win32com.client.Dispatch('Outlook.Application')
        mail = outlook.CreateItem(0)
        # Set email properties
        to_addresses =  ';'.join(
            set(
                suspended_extract_refresh_tasks.get('Content owner email', pd.Series([])).to_list()
                + suspended_flow_tasks.get('Flow owner email', pd.Series([])).to_list()
                + suspended_subscription_tasks.get('Content owner email', pd.Series([])).to_list()
            )
        )
        cc_addresses = ';'.join(
            [
                'sqlshortreads@gmail.com',
            ]
        )
        mail.To = to_addresses
        mail.CC = cc_addresses
        mail.Subject = 'ACTION REQUIRED - TABLEAU TASKS SUSPENDED'
        mail.HTMLBody = f"""
        You're receiving this email because you own a task that has been suspended on 
        the Tableau Server due to consecutive failures. Please make any corrections 
        required and resume the task or delete the task.
        <html>
        <head>
            <style>
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    font-family: Arial, sans-serif;
                }}
                th, td {{
                    padding: 8px;
                    text-align: left;
                }}
                th {{
                    background-color: #f2f2f2;
                    font-weight: bold;
                }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
            </style>
        </head>
        <body>

            <h2>Suspended tasks report ({sum(dataframe.shape[0] for dataframe in [suspended_extract_refresh_tasks, suspended_flow_tasks, suspended_subscription_tasks])} tasks)</h2>

            <h3>Extract refresh tasks ({suspended_extract_refresh_tasks.shape[0]})</h3>
            {suspended_extract_refresh_tasks.to_html(index=False, border=0)}

            <h3>Flow tasks ({suspended_flow_tasks.shape[0]})</h3>
            {suspended_flow_tasks.to_html(index=False, border=0)}

            <h3>Subscriptions tasks ({suspended_subscription_tasks.shape[0]})</h3>
            {suspended_subscription_tasks.to_html(index=False, border=0)}

        </body>
        </html>
        """
        mail.Send()
    except Exception as email_error:
        streamlit.error(f'Failed to send email. Error: {email_error}')
    else:
        streamlit.success('Email reminders sent successfully!')
    finally:
        pythoncom.CoUninitialize()

def add_extract_refresh_context(base_server_url: str, headers: dict, verify_certificate: bool, suspended_extract_refresh_tasks: pd.DataFrame) -> pd.DataFrame:
    """
    Enriches the data gathered for suspended extract refresh tasks.

    The content (i.e., data source or workbook) name and the content owner email are made available
    for each suspended extract refresh task.

    Args:
        base_server_url: The base URL portion of the full Tableau Server or Tableau Cloud instance URL input.
        headers (dict): Contains key pieces of information originating from the intitial sign-in response.
            The site LUID, token, and response format (JSON) are captured within this dictionary.
        verify_certificate (bool): Indicates whether the server's SSL/TLS certificate should be verified.
            By default, this option will be enabled to mitigate security risks. If the server contains a
            self-signed certificate, then this box can be unchecked.
        suspended_extract_refresh_tasks (pd.DataFrame): A dataframe containing information on each suspended
            extract task.
    Returns:
        suspended_extract_refresh_tasks (pd.DataFrame): A dataframe containing the original supsended extract
            refresh task information gathered along with additional context (e.g., content owner email).
    """
    # Configure data sources request options.
    fields_required = 'datasource.id,datasource.name,owner.email'
    page_size = 100
    page_number = 1
    items_returned = 0
    request_complete = False
    all_data_sources = []
    while not request_complete:
        get_data_sources_url = f"{base_server_url}/api/3.24/sites/{headers['site_luid']}/datasources?pageSize={page_size}&pageNumber={page_number}&fields={fields_required}"
        get_data_sources_request = requests.get(get_data_sources_url, headers=headers, verify=verify_certificate)
        get_data_sources_response = json.loads(get_data_sources_request.content)
        if get_data_sources_response:
            data_sources = get_data_sources_response['datasources']['datasource']
            all_data_sources.extend(
                [
                    {
                        'Content ID': data_source.get('id'),
                        'Content name': data_source.get('name'),
                        'Content URL': data_source.get('webpageUrl'),
                        'Content owner email': data_source.get('owner').get('email')
                    }
                    for data_source in data_sources
                ]
            )
            page_number += 1
            items_returned += page_size
            # Determine whether all relevant dat a sources have been retrieved. 
            if items_returned >= int(get_data_sources_response['pagination']['totalAvailable']):
                request_complete = True
    # Create a dataframe containing necessary context for each data source.
    data_source_context = pd.DataFrame(data=all_data_sources)

    # Configure workbooks request options.
    fields_required = 'workbook.id,workbook.name,owner.email'
    page_size = 100
    page_number = 1
    items_returned = 0
    request_complete = False
    all_workbooks = []
    while not request_complete:
        get_workbooks_url = f"{base_server_url}/api/3.24/sites/{headers['site_luid']}/workbooks?pageSize={page_size}&pageNumber={page_number}&fields={fields_required}"
        get_workbooks_request = requests.get(get_workbooks_url, headers=headers, verify=verify_certificate)
        get_workbooks_response = json.loads(get_workbooks_request.content)
        if get_workbooks_response:
            workbooks = get_workbooks_response['workbooks']['workbook']
            all_workbooks.extend(
                [
                    {
                        'Content ID': workbook.get('id'),
                        'Content name': workbook.get('name'),
                        'Content URL': workbook.get('webpageUrl'),
                        'Content owner email': workbook.get('owner').get('email')
                    }
                    for workbook in workbooks
                ]
            )
            page_number += 1
            items_returned += page_size
            # Determine whether all relevant workbooks have been retrieved. 
            if items_returned >= int(get_workbooks_response['pagination']['totalAvailable']):
                request_complete = True
    # Create a dataframe containing necessary context for each workbook.
    workbook_context = pd.DataFrame(data=all_workbooks)

    # Combine the data source context and workbook context dataframes and add the necessary context to each suspended extract refresh task.
    extract_refresh_context = pd.concat([data_source_context, workbook_context], ignore_index=True)
    suspended_extract_refresh_tasks = (
        suspended_extract_refresh_tasks
        .merge(
            right=extract_refresh_context,
            how='inner',
            left_on='Extract ID',
            right_on='Content ID'
        )
        .drop(columns=['Content ID'])
    )
    return suspended_extract_refresh_tasks

def add_flow_context(base_server_url: str, headers: dict, verify_certificate: bool, suspended_flow_tasks: pd.DataFrame) -> pd.DataFrame:
    """
    Enriches the data gathered for suspended flow tasks by including the flow owner email.

    Args:
        base_server_url: The base URL portion of the full Tableau Server or Tableau Cloud instance URL input.
        headers (dict): Contains key pieces of information originating from the intitial sign-in response.
            The site LUID, token, and response format (JSON) are captured within this dictionary.
        verify_certificate (bool): Indicates whether the server's SSL/TLS certificate should be verified.
            By default, this option will be enabled to mitigate security risks. If the server contains a
            self-signed certificate, then this box can be unchecked.
        suspended_flow_tasks (pd.DataFrame): A dataframe containing information on each suspended flow task.
    Returns:
        suspended_flow_tasks (pd.DataFrame): A dataframe containing the original supsended flow task information
            gathered along with the flow owner's email address.
    """
    # Configure flows request options.
    page_size = 100
    page_number = 1
    items_returned = 0
    request_complete = False
    all_flows = []
    while not request_complete:
        get_flows_url = f"{base_server_url}/api/3.24/sites/{headers['site_luid']}/flows?pageSize={page_size}&pageNumber={page_number}"
        get_flows_request = requests.get(get_flows_url, headers=headers, verify=verify_certificate)
        get_flows_response = json.loads(get_flows_request.content)
        if get_flows_response:
            flows = get_flows_response['flows']['flow']
            all_flows.extend(
                [
                    {
                        'Flow ID': flow.get('id'),
                        'Flow URL': flow.get('webpageUrl'),
                        'Flow owner email': flow.get('owner').get('email')
                    }
                    for flow in flows
                ]
            )
            page_number += 1
            items_returned += page_size
            # Determine whether all relevant flows have been retrieved. 
            if items_returned >= int(get_flows_response['pagination']['totalAvailable']):
                request_complete = True
    
    # Create a dataframe containing necessary context for each flow.
    flow_context = pd.DataFrame(data=all_flows)    
    suspended_flow_tasks = (
        suspended_flow_tasks
        .merge(
            right=flow_context,
            how='inner',
            left_on='Flow ID',
            right_on='Flow ID'
        )
    )
    return suspended_flow_tasks

def add_subscription_context(base_server_url: str, headers: dict, verify_certificate: bool, suspended_subscription_tasks: pd.DataFrame) -> pd.DataFrame:
    """
    Enriches the data gathered for suspended subscription tasks.

    The content (i.e., workbook or view) name and the content owner email are made available
    for each suspended subscription task.

    Args:
        base_server_url: The base URL portion of the full Tableau Server or Tableau Cloud instance URL input.
        headers (dict): Contains key pieces of information originating from the intitial sign-in response.
            The site LUID, token, and response format (JSON) are captured within this dictionary.
        verify_certificate (bool): Indicates whether the server's SSL/TLS certificate should be verified.
            By default, this option will be enabled to mitigate security risks. If the server contains a
            self-signed certificate, then this box can be unchecked.
        suspended_subscription_tasks (pd.DataFrame): A dataframe containing information on each suspended
            subscription task.
    Returns:
        suspended_subscription_tasks (pd.DataFrame): A dataframe containing the original supsended subscription
            task information gathered along with additional context (e.g., content owner email).
    """
    # Configure workbooks request options.
    fields_required = 'workbook.id,workbook.name,owner.email'
    page_size = 100
    page_number = 1
    items_returned = 0
    request_complete = False
    all_workbooks = []
    while not request_complete:
        get_workbooks_url = f"{base_server_url}/api/3.24/sites/{headers['site_luid']}/workbooks?pageSize={page_size}&pageNumber={page_number}&fields={fields_required}"
        get_workbooks_request = requests.get(get_workbooks_url, headers=headers, verify=verify_certificate)
        get_workbooks_response = json.loads(get_workbooks_request.content)
        if get_workbooks_response:
            workbooks = get_workbooks_response['workbooks']['workbook']
            all_workbooks.extend(
                [
                    {
                        'Content ID': workbook.get('id'),
                        'Content name': workbook.get('name'),
                        'Content URL': workbook.get('webpageUrl'),
                        'Content owner email': workbook.get('owner').get('email')
                    }
                    for workbook in workbooks
                ]
            )
            page_number += 1
            items_returned += page_size
            # Determine whether all relevant workbooks have been retrieved. 
            if items_returned >= int(get_workbooks_response['pagination']['totalAvailable']):
                request_complete = True
    # Create a dataframe containing necessary context for each workbook.
    workbook_context = pd.DataFrame(data=all_workbooks)

    # Configure views request options.
    fields_required = 'view.id,view.name,workbook.name,owner.email'
    page_size = 100
    page_number = 1
    items_returned = 0
    request_complete = False
    all_views = []
    while not request_complete:
        get_views_url = f"{base_server_url}/api/3.24/sites/{headers['site_luid']}/views?pageSize={page_size}&pageNumber={page_number}&fields={fields_required}"
        get_views_request = requests.get(get_views_url, headers=headers, verify=verify_certificate)
        get_views_response = json.loads(get_views_request.content)
        if get_views_response:
            views = get_views_response['views']['view']
            all_views.extend(
                [
                    {
                        'Content ID': view.get('id'),
                        'Content name': f"{view.get('name')} ({view.get('workbook').get('name')})",
                        'Content URL': view.get('contentUrl'),
                        'Content owner email': view.get('owner').get('email')
                    }
                    for view in views
                ]
            )
            page_number += 1
            items_returned += page_size
            # Determine whether all relevant views have been retrieved. 
            if items_returned >= int(get_views_response['pagination']['totalAvailable']):
                request_complete = True

    # Create a dataframe containing necessary context for each workbook view.
    view_context = pd.DataFrame(data=all_views)
    # Combine the view and workbook context dataframes and add the necessary context to each suspended subscription task.
    subscription_context = pd.concat([view_context, workbook_context], ignore_index=True)
    suspended_subscription_tasks = (
        suspended_subscription_tasks
        .merge(
            right=subscription_context,
            how='inner',
            left_on='Content ID',
            right_on='Content ID'
        )
    )   
    return suspended_subscription_tasks

def get_suspended_tasks(base_server_url: str, headers: dict, verify_certificate: bool, task_failure_limit: int = 5) -> tuple[pd.DataFrame]:
    """
    Retrieve all suspended tasks.

    Args:
        base_server_url: The base URL portion of the full Tableau Server or Tableau Cloud instance URL input.
        headers (dict): The dictionary containing the header information for subsequent API requests.
            This also includes the site LUID for the request URLs.
        verify_certificate (bool): Indicates whether the server's SSL/TLS certificate should be verified.
            By default, this option will be enabled to mitigate security risks. If the server contains a
            self-signed certificate, then this box can be unchecked.
        task_failure_limit (int): The number of times a task can consecutively fail prior to being suspended.

    Returns:
        suspended_extract_refresh_tasks, suspended_flow_tasks, suspended_subscription_tasks (tuple[pd.DataFrame]): A tuple of dataframes containing suspended tasks, if any.
    """
    # Retrieve all suspended extract refresh tasks.
    get_extract_refresh_tasks_url = f"{base_server_url}/api/3.24/sites/{headers['site_luid']}/tasks/extractRefreshes?fields=owner.email"
    get_extract_refresh_tasks_request = requests.get(get_extract_refresh_tasks_url, headers=headers, verify=verify_certificate)
    get_extract_refresh_tasks_response = json.loads(get_extract_refresh_tasks_request.content)
    if get_extract_refresh_tasks_response:
        extract_refresh_tasks = get_extract_refresh_tasks_response['tasks']['task']
        suspended_extract_refresh_tasks = pd.DataFrame(
            data=[
                {
                    'Extract ID': extract_refresh['extractRefresh'].get('datasource',  extract_refresh['extractRefresh'].get('workbook')).get('id'),
                    'Extract type': 'Data source' if extract_refresh['extractRefresh'].get('datasource') else 'Workbook',
                    'Failure count': int(extract_refresh['extractRefresh']['consecutiveFailedCount'])
                }
                for extract_refresh in extract_refresh_tasks
                if int(extract_refresh['extractRefresh']['consecutiveFailedCount']) == task_failure_limit
            ]
        )
    else:
        suspended_extract_refresh_tasks = pd.DataFrame()

    # Retrieve all suspended flow tasks.
    get_flow_tasks_url = f"{base_server_url}/api/3.24/sites/{headers['site_luid']}/tasks/runFlow"
    get_flow_tasks_request = requests.get(get_flow_tasks_url, headers=headers, verify=verify_certificate)
    get_flow_tasks_response = json.loads(get_flow_tasks_request.content)
    if get_flow_tasks_response:
        flow_tasks = get_flow_tasks_response['tasks']['task']
        suspended_flow_tasks = pd.DataFrame(
            data=[
                {
                    'Flow ID': flow['flowRun']['flow']['id'],
                    'Flow name': flow['flowRun']['flow']['name'],
                    'Task type': 'Linked task' if flow['flowRun']['schedule']['type'] == 'System' else 'Flow',
                    'Failure count': int(flow['flowRun']['consecutiveFailedCount'])
                }
                for flow in flow_tasks
                if int(flow['flowRun']['consecutiveFailedCount']) == task_failure_limit
            ]
        )
    else:
        suspended_flow_tasks = pd.DataFrame()

    # Retrieve all suspended subscriptions.
    # Configure suspended subscription task request options.
    page_size = 100
    page_number = 1
    items_returned = 0
    request_complete = False
    suspended_subscription_tasks = []
    while not request_complete:
        get_subscription_tasks_url = f"{base_server_url}/api/3.24/sites/{headers['site_luid']}/subscriptions?pageSize={page_size}&pageNumber={page_number}"
        get_subscription_tasks_request = requests.get(get_subscription_tasks_url, headers=headers, verify=verify_certificate)
        get_subscription_tasks_response = json.loads(get_subscription_tasks_request.content)
        if get_subscription_tasks_response:
            subscription_tasks = get_subscription_tasks_response['subscriptions']['subscription']
            # Add only those subscriptions which are suspended.
            suspended_subscription_tasks.extend(
                [
                    {
                        'Subscription ID': subscription.get('id'),
                        'Subject': subscription.get('subject'),
                        'Recipient ID': subscription.get('user').get('id'),
                        'Recipient name': subscription.get('user').get('name'),
                        'Content ID': subscription.get('content').get('id'),
                        'Content type': subscription.get('content').get('type')
                    }
                    for subscription in subscription_tasks
                    if subscription['suspended'] == True
                ]
            )
            page_number += 1
            items_returned += page_size
            # Determine whether all subscriptions have been retrieved. 
            if items_returned >= int(get_subscription_tasks_response['pagination']['totalAvailable']):
                request_complete = True
    suspended_subscription_tasks = pd.DataFrame(data=suspended_subscription_tasks)

    return suspended_extract_refresh_tasks, suspended_flow_tasks, suspended_subscription_tasks

def display_suspended_tasks(suspended_extract_refresh_tasks: pd.DataFrame, suspended_flow_tasks: pd.DataFrame, suspended_subscription_tasks: pd.DataFrame) -> None:
    """
    Display the suspended tasks.

    Suspended extract refresh tasks, flow tasks, and subscription tasks are displayed in individual tabs.

    Args:
    suspended_extract_refresh_tasks (pd.DataFrame): A dataframe containing suspended extract refresh tasks.
    suspended_flow_tasks (pd.DataFrame): A dataframe containing suspended flow tasks.
    suspended_subscription_tasks (pd.DataFrame): A dataframe containing suspended subscription tasks.

    Returns:
        None
    """    
    if all([suspended_extract_refresh_tasks.empty, suspended_flow_tasks.empty, suspended_subscription_tasks.empty]):
        return streamlit.info('No extract refresh tasks, flow tasks, or subscription tasks are currently suspended.')
    
    task_type_tabs = streamlit.tabs(
        tabs=[
            f'Extract refresh tasks ({suspended_extract_refresh_tasks.shape[0]})',
            f'Flow tasks ({suspended_flow_tasks.shape[0]})',
            f'Subscriptions tasks ({suspended_subscription_tasks.shape[0]})'
        ]
    )
    for task_type, suspended_tasks in zip(task_type_tabs, [suspended_extract_refresh_tasks, suspended_flow_tasks, suspended_subscription_tasks]):
        with task_type:
            if not suspended_tasks.empty:
                streamlit.dataframe(
                    data=suspended_tasks,
                    hide_index=True,
                    column_config={
                        'Content URL': streamlit.column_config.LinkColumn(),
                        'Flow URL': streamlit.column_config.LinkColumn()
                    }
                )
            else:
                streamlit.info('No tasks of this type are currently suspended.')
    return None

# Initialize session state variables.
if 'FULL_SERVER_URL' not in streamlit.session_state:
    streamlit.session_state['FULL_SERVER_URL'] = None
if 'BASE_SERVER_URL' not in streamlit.session_state:
    streamlit.session_state['BASE_SERVER_URL'] = None
if 'INSTANCE_TYPE' not in streamlit.session_state:
    streamlit.session_state['INSTANCE_TYPE'] = None
if 'SITE_ID' not in streamlit.session_state:
    streamlit.session_state['SITE_ID'] = None
if 'TOKEN_NAME' not in streamlit.session_state:
    streamlit.session_state['TOKEN_NAME'] = None
if 'TOKEN_VALUE' not in streamlit.session_state:
    streamlit.session_state['TOKEN_VALUE'] = None
if 'VERIFY_CERTIFICATE' not in streamlit.session_state:
    streamlit.session_state['VERIFY_CERTIFICATE'] = None
if 'TASK_FAILURE_LIMIT' not in streamlit.session_state:
    streamlit.session_state['TASK_FAILURE_LIMIT'] = None
if 'fetch_suspended_tasks_button_enabled' not in streamlit.session_state:
    streamlit.session_state['fetch_suspended_tasks_button_enabled'] = False
if 'send_email_reminder_button_enabled' not in streamlit.session_state:
    streamlit.session_state['send_email_reminder_button_enabled'] = False
if 'suspended_extract_refresh_tasks' not in streamlit.session_state:
    streamlit.session_state['suspended_extract_refresh_tasks'] = None
if 'suspended_flow_tasks' not in streamlit.session_state:
    streamlit.session_state['suspended_flow_tasks'] = None
if 'suspended_subscription_tasks' not in streamlit.session_state:
    streamlit.session_state['suspended_subscription_tasks'] = None

# Configure browser page.
streamlit.set_page_config(
    page_title="Fetch suspended tasks",
    page_icon=":incoming_envelope:",
)
# Add title.
streamlit.title(
    body='Fetch suspended tasks',
    help=(
        "This utility allows a user to quickly notify the owners of suspended flow tasks, extract refresh tasks,  "
        "and subscription tasks. Tasks are in a suspended state when the task consecutively fails for a number  "
        "of times. By default, the consecutive failure limit for tasks prior to suspension is 5; however, this value "
        "can be adjusted by a server administrator."
    ),
    anchor=False
)

# Configure user-input fields for the authentication section of the UI.
authentication_container = streamlit.container(border=True)
with authentication_container:
    streamlit.subheader(body='Authentication', anchor=False, divider='grey')
    streamlit.session_state['FULL_SERVER_URL'] = streamlit.text_input(
        label='Server URL',
        value='',
        placeholder='Enter a server url.',
        help=(
            """
            Enter the URL corresponding to your Tableau Server or Tableau Cloud instance.  
            This URL must start with "https://". If you use the default site, then the server
            url will match the base URL.

            Example full server URL: https://10ax.online.tableau.com/#/site/sqlshortreads/home  
            Base URL: https://10ax.online.tableau.com/  
            Site ID: sqlshortreads
            """
        ),
        on_change=is_fetch_suspended_tasks_button_enabled
    )
    # Extract base URL from the full server URL provided by the user.
    if streamlit.session_state['FULL_SERVER_URL']:
        streamlit.session_state['BASE_SERVER_URL'] = extract_base_server_url(streamlit.session_state['FULL_SERVER_URL'])

    verify_certificate = streamlit.checkbox(
        label='Verify SSL/TLS certificate',
        value=True,
        help=(
            """
            Specify whether the server's SSL/TLS certificate should be verified.
            By default, this option will be enabled to mitigate security risks.
            If the server contains a self-signed certificate, then this box can
            be unchecked.
            """
        )
    )
    if verify_certificate:
        streamlit.session_state['VERIFY_CERTIFICATE'] = True
    else:
        streamlit.session_state['VERIFY_CERTIFICATE'] = False

    instance_type, site_id = streamlit.columns(2)
    with instance_type:
        streamlit.session_state['INSTANCE_TYPE'] = streamlit.selectbox(
            label='Instance type',
            options=['Tableau Server', 'Tableau Cloud'],
            help=(
                """
                Select the type of instance being used given the options of
                Tableau Server or Tableau Cloud. If the base URL ends in
                "online.tableau.com," then it is likely that the instance
                is of Tableau Cloud type. This is necessary because Tableau's
                REST API endpoints provide responses that can vary depending 
                on the instance type.
                """
            ),
            on_change=is_fetch_suspended_tasks_button_enabled
        )
    with site_id:
        streamlit.session_state['SITE_ID'] = streamlit.text_input(
            label='Site ID',
            value=extract_site_id(streamlit.session_state['FULL_SERVER_URL']),
            help=(
                """
                This value corresponds to the site ID value extracted from the full server URL
                provided in the "Server URL" field. If you do not have multiple sites associated
                with your Tableau Server or Tableau Cloud instance or use the default site, then
                this field should be blank / empty.

                The site ID can be found within the URL associated with a Tableau Server or Cloud instance.

                In the following example URL, "sqlshortreads" is the site ID.  
                https://10ax.online.tableau.com/#/site/sqlshortreads/home
                """
            ),
            disabled=True
        )

    token_name, token_value = streamlit.columns(2)
    with token_name:
        streamlit.session_state['TOKEN_NAME'] = streamlit.text_input(
            label='Token name',
            value='',
            placeholder='Enter a token name.',
            help=(
                """
                Enter the name of your personal access token. You can find the name of your
                person access token within your account settings. This value is case-sensitive.
                """
            ),
            on_change=is_fetch_suspended_tasks_button_enabled
        )
    with token_value:
        streamlit.session_state['TOKEN_VALUE'] = streamlit.text_input(
            label='Token value',
            value='',
            placeholder='Enter a token value.',
            help=(
                """
                Enter your personal access token value. This value would have been generated
                at the time of token creation within your account settings. This value is case-sensitive.
                """
            ),
            type='password',
            on_change=is_fetch_suspended_tasks_button_enabled
        )

# Configure user-input fields for the settings section of the UI.
settings_container = streamlit.container(border=True)
with settings_container:
    streamlit.subheader(body='Settings', anchor=False, divider='grey')
    streamlit.session_state['TASK_FAILURE_LIMIT'] = streamlit.number_input(
        label='Task failure limit',
        value=5,
        placeholder="Enter your server's task failure limit.",
        help=(
            """
            Enter your server's task failure limit. This is the number of times a tasks can consecutively
            fail prior to being suspended.
            """
        ),
        on_change=is_fetch_suspended_tasks_button_enabled
    )

# Configure custom button properties using markdown.
streamlit.markdown(
    """
    <style>
    .stButton>button {
        background-color: #1d4f91;  /* Dark blue background for enabled state */
        color: white;  /* White text */
        border: none;  /* Remove borders */
        padding: 10px 20px;  /* Add padding */
        text-align: center;  /* Center the text */
        font-size: 16px;  /* Increase font size */
        border-radius: 5px;  /* Add rounded corners */
        cursor: pointer;  /* Pointer cursor for enabled button */
        transition: background-color 0.3s ease; /* Smooth transition for color changes */
    }
    .stButton>button:disabled {
        background-color: #a5b9d3 !important;  /* Light blue background for disabled state */
        color: white !important;  /* Ensure text remains white */
        cursor: not-allowed;  /* Not-allowed cursor for disabled button */
        opacity: 1;  /* Keep full opacity for a consistent design */
    }
    .stButton>button:disabled:active,
    .stButton>button:disabled:hover,
    .stButton>button:disabled:focus {
        background-color: #a5b9d3 !important;  /* Keep the disabled color */
        color: white !important;  /* Ensure text remains white */
        transform: none;  /* No transformation on click */
    }
    .stButton>button:active {
        background-color: #0f3761 !important;  /* Darker shade when clicked */
        color: white !important;  /* Ensure text remains white */
        transform: scale(0.95);  /* Slightly shrink the button to indicate click */
    }
    .stButton>button:hover {
        background-color: #163d73 !important;  /* Slightly darker blue on hover */
        color: white !important;  /* Ensure text remains white */
    }
    .stButton>button:focus {
        background-color: #1d4f91 !important;  /* Retain dark blue when focused */
        color: white !important;  /* Ensure text remains white */
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Create a mechanism for enabling / disabling the fetch suspended tasks and send email reminder buttons.
streamlit.session_state['fetch_suspended_tasks_button_enabled'] = is_fetch_suspended_tasks_button_enabled()
fetch_suspended_tasks_button, send_email_reminder_button = streamlit.columns(2, gap='large')
with fetch_suspended_tasks_button:
    # Create fetch suspended tasks button.
    fetch_suspended_tasks_button = streamlit.button(
        label='Fetch suspended tasks',
        icon='🔍',
        disabled=not streamlit.session_state['fetch_suspended_tasks_button_enabled'],
        use_container_width=True
    )
    # If the button is pressed/clicked, all required fields are populated, and access has been verified, then fetch the suspended tasks.
    if is_fetch_suspended_tasks_button_enabled() and fetch_suspended_tasks_button:
        # Verify user has access to the specified Tableau Server or Tableau Cloud instance.
        headers = sign_in(
            streamlit.session_state['BASE_SERVER_URL'],
            streamlit.session_state['SITE_ID'],
            streamlit.session_state['TOKEN_NAME'],
            streamlit.session_state['TOKEN_VALUE'],
            streamlit.session_state['VERIFY_CERTIFICATE']
        )
        # If the user has access to the instance, then retrieve the suspended tasks, type by type.
        if headers:
        # Display the results of the flow restoration process.
            with streamlit.spinner(text='Fetching suspended tasks...', show_time=True):
                time.sleep(1)
                streamlit.session_state['suspended_extract_refresh_tasks'], streamlit.session_state['suspended_flow_tasks'], streamlit.session_state['suspended_subscription_tasks'] = get_suspended_tasks(
                    streamlit.session_state['BASE_SERVER_URL'],
                    headers,
                    streamlit.session_state['VERIFY_CERTIFICATE'],
                    streamlit.session_state['TASK_FAILURE_LIMIT']
                )
                if not streamlit.session_state['suspended_extract_refresh_tasks'].empty:
                    streamlit.session_state['suspended_extract_refresh_tasks'] = add_extract_refresh_context(
                        streamlit.session_state['BASE_SERVER_URL'],
                        headers,
                        streamlit.session_state['VERIFY_CERTIFICATE'],
                        streamlit.session_state['suspended_extract_refresh_tasks']
                    )
                if not streamlit.session_state['suspended_flow_tasks'].empty:
                    streamlit.session_state['suspended_flow_tasks'] = add_flow_context(
                        streamlit.session_state['BASE_SERVER_URL'],
                        headers,
                        streamlit.session_state['VERIFY_CERTIFICATE'],
                        streamlit.session_state['suspended_flow_tasks']
                    )
                if not streamlit.session_state['suspended_subscription_tasks'].empty:        
                    streamlit.session_state['suspended_subscription_tasks'] = add_subscription_context(
                        streamlit.session_state['BASE_SERVER_URL'],
                        headers,
                        streamlit.session_state['VERIFY_CERTIFICATE'],
                        streamlit.session_state['suspended_subscription_tasks']
                    )

            # Sign-out of Tableau Server or Tableau Cloud instance.
            sign_out(
                streamlit.session_state['BASE_SERVER_URL'],
                headers,
                streamlit.session_state['VERIFY_CERTIFICATE']
            )

# Display suspended tasks by type across individual, corresponding tabs.
if not all(
    [
        streamlit.session_state['suspended_extract_refresh_tasks'] is None,
        streamlit.session_state['suspended_flow_tasks'] is None,
        streamlit.session_state['suspended_subscription_tasks'] is None
    ]
):
    display_suspended_tasks(
        streamlit.session_state['suspended_extract_refresh_tasks'],
        streamlit.session_state['suspended_flow_tasks'],
        streamlit.session_state['suspended_subscription_tasks']
    )

# Create a mechanism for enabling / disabling the fetch suspended tasks and send email reminder buttons.
with send_email_reminder_button:
    streamlit.session_state['send_email_reminder_button_enabled'] = is_send_email_reminder_button_enabled()
    # Create send email reminder button.
    send_email_reminder_button = streamlit.button(
        label='Send email reminder',
        icon='📧',
        disabled=not streamlit.session_state['send_email_reminder_button_enabled'],
        use_container_width=True
    )

if streamlit.session_state['send_email_reminder_button_enabled'] and send_email_reminder_button:
    # If the button is pressed/clicked, then send an email reminder to each of the task owners for each suspended task type.
    with streamlit.spinner(text='Sending email reminders...', show_time=True):
        time.sleep(1)
        send_email(
            streamlit.session_state['suspended_extract_refresh_tasks'],
            streamlit.session_state['suspended_flow_tasks'],
            streamlit.session_state['suspended_subscription_tasks']
        )
