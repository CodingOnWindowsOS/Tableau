import json
import pandas as pd
import re
import requests
import streamlit
import tableauserverclient as tsc
import time
import urllib3

# Suppress warning produced from opting to not verify certificate.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def verify_access(server: tsc.Server, tableau_authentication: tsc.PersonalAccessTokenAuth) -> bool:
    """
    Verifies the user has access to the Tableau Server or Tableau Cloud instance.

    Args:
        server (tsc.Server): The connected Tableau Server or Cloud instance.
        tableau_authentication (tsc.PersonalAccessTokenAuth): The authentication mechanism for connecting
            to the Tableau Server or Cloud instance.

    Returns:
        boolean: True if access verified, otherwise False.    
    """
    try:
        server.auth.sign_in(tableau_authentication)
        server.auth.sign_out()
    except tsc.NotSignedInError:
        streamlit.error(f"Unable to sign-in to {streamlit.session_state['FULL_SERVER_URL']}. Please verify the server URL, token name, and token value are correct.")
        return False
    else:
        return True

def valid_user(server: tsc.Server, tableau_authentication: tsc.PersonalAccessTokenAuth, value: str, user_type: str) -> tsc.UserItem | bool:
    """
    Verifies the user exists on the Tableau Server or Tableau Cloud instance.

    Args:
        server (tsc.Server): The connected Tableau Server or Cloud instance.
        tableau_authentication (tsc.PersonalAccessTokenAuth): The authentication mechanism for connecting
            to the Tableau Server or Cloud instance.
        value (str): The user ID value. This is usually the login ID or email address.
        user_type (str): Source or target.

    Returns:
        tsc.UserItem if the user exists, False otherwise.
    """
    with server.auth.sign_in(tableau_authentication):
        user = server.users.filter(name=value)
        if user:
            return user[0]
        else:
            streamlit.write(f'{user_type.title()} user {value} does not exist.')
            return False

def get_favorites(server: tsc.Server, tableau_authentication: tsc.PersonalAccessTokenAuth, user_name: str) -> dict:
    """
    Retrieve the user's favorites.

    Args:
        server (tsc.Server): The connected Tableau Server or Cloud instance.
        tableau_authentication (tsc.PersonalAccessTokenAuth): The authentication mechanism for connecting
            to the Tableau Server or Cloud instance.
        user_name (str): The user name value for which the favorites are to be retrieved.

    Returns:
        A dictionary containing the user's favorites, if any.
    """
    with server.auth.sign_in(tableau_authentication):
        user = server.users.filter(name=user_name)
        user = user[0]
        server.users.populate_favorites(user)
        user.favorites['datasource'] = user.favorites.pop('datasources')
        user.favorites['flow'] = user.favorites.pop('flows')
        user.favorites['metric'] = user.favorites.pop('metrics')
        user.favorites['project'] = user.favorites.pop('projects')
        user.favorites['view'] = user.favorites.pop('views')
        user.favorites['workbook'] = user.favorites.pop('workbooks')
        return {favorite_type: favorite_items for favorite_type, favorite_items in user.favorites.items() if favorite_items}

def mirror_favorites(server: tsc.Server, tableau_authentication: tsc.PersonalAccessTokenAuth, source_user_favorites: dict, target_user_item: tsc.UserItem) -> None:
    """
    Mirrors the source user's favorites by creating identical favorites for the target user.

    Args:
        server (tsc.Server): The connected Tableau Server or Cloud instance.
        tableau_authentication (tsc.PersonalAccessTokenAuth): The authentication mechanism for connecting
            to the Tableau Server or Cloud instance.
        source_user_favorites (dict): A dictionary containing the user's favorited items. The favorite types
            are the keys and the values are the corresponding favorited items of the respective type.
        target_user_item (tsc.UserItem): The user for which favorites will be created for in the process of
        mirroring the source user's favorites.

    Returns:
        None
    """
    progress_text = 'Mirroring content...'
    progress_bar = streamlit.progress(value=0, text=progress_text)
    total_favorites = sum(len(favorites) for favorites in source_user_favorites.values())
    favorites_remaining = total_favorites
    with server.auth.sign_in(tableau_authentication):
        for favorite_type, favorite_items in source_user_favorites.items():
            for favorite_item in favorite_items:
                server.favorites.add_favorite(user_item=target_user_item, content_type=favorite_type, item=favorite_item)
                favorites_remaining -= 1
                progress_bar.progress(
                    1 - (favorites_remaining / total_favorites),
                    text=f'{round((1 - (favorites_remaining / total_favorites)) * 100)}% complete'
                )
        # Clear the progress bar after flow restoration process is complete.
        time.sleep(1)
        progress_bar.empty()
        return None

def display_favorites(server: tsc.Server, tableau_authentication: tsc.PersonalAccessTokenAuth, target_user: tsc.UserItem, target_user_favorites: dict) -> None:
    """
    Display the target user's favorites.

    Favorites are displayed accross their respective content type (e.g., workbook, data sources, etc.)
    tab.

    Args:
    server (tsc.Server): The connected Tableau Server or Cloud instance.
    tableau_authentication (tsc.PersonalAccessTokenAuth): The authentication mechanism for connecting
        to the Tableau Server or Cloud instance.
    target_user_item (tsc.UserItem): The user for which favorites have been created for in the mirroring
        process.
    target_user_favorites (tsc.UserItem): A dictionary containing the user's favorited items. The favorite types
        are the keys and the values are the corresponding favorited items of the respective type.

    Returns:
        None
    """
    with server.auth.sign_in(tableau_authentication):
        project_info = pd.DataFrame(
            data=[(project.id, project.name) for project in tsc.Pager(server.projects)],
            columns=['Project ID', 'Project Name']
        )
    favorite_types = target_user_favorites.keys()
    favorite_tabs = streamlit.tabs([f'{favorite_type.upper()} ({len(favorites)})' for favorite_type, favorites in target_user_favorites.items()])
    # favorite_tabs = streamlit.tabs([favorite_type.upper() for favorite_type in target_user_favorites.keys()])
    for favorite_tab, (favorite_type, favorite_items) in zip(favorite_tabs, target_user_favorites.items()):
        with favorite_tab:
            favorite_data = (
                pd.DataFrame(
                    data={
                        'Content ID': [favorite.id for favorite in favorite_items],
                        'Content Name': [favorite.name for favorite in favorite_items],
                        'Project ID': [
                            favorite.project_id 
                            if favorite_type != 'project'
                            else favorite.parent_id
                            for favorite in favorite_items
                        ]
                    }
                ).merge(
                    right=project_info,
                    how='inner',
                    left_on='Project ID',
                    right_on='Project ID'
                )
            )
            streamlit.dataframe(data=favorite_data[['Content Name', 'Project Name', 'Content ID', 'Project ID']], hide_index=True)
    return None

def get_subscriptions(base_server_url: str, site_id: str, token_name: str, token_value: str, user_name: str) -> list[dict]:
    """
    Retrieve the user's subscriptions.

    Args:
        base_server_url: The base URL portion of the full Tableau Server or Tableau Cloud instance URL input.
        site_id (str): The site ID value correspond the the Tableau Server or Tableau Cloud instance.
        token_name (str): The name of the personal access token configured.
        token_value (str): The secret value corresponding to the personal access token configured.
        user_name (str): The user name value for which the subscriptions are to be retrieved.

    Returns:
        user_subscriptions (list[dict]): A list of dictionaries capturing the user's subscriptions, if any.
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
    sign_in_request = requests.post(sign_in_url, json=payload, headers=headers, verify=False)
    # Convert response to dictionary to extract the token and site ID for the subsequent subscription request.
    sign_in_response = json.loads(sign_in_request.content)
    token = sign_in_response['credentials']['token']
    site_luid = sign_in_response['credentials']['site']['id']
    headers['X-tableau-auth'] = token

    # Configure subscription request.
    page_size = 100
    page_number = 1
    items_returned = 0
    request_complete = False
    user_subscriptions = []
    # Retrieve all subscriptions.
    while not request_complete:
        get_subscriptions_url = f'{base_server_url}/api/3.24/sites/{site_luid}/subscriptions?pageSize={page_size}&pageNumber={page_number}'
        get_subscriptions_request = requests.get(get_subscriptions_url, headers=headers, verify=False)
        get_subscriptions_response = json.loads(get_subscriptions_request.content)
        if not get_subscriptions_response['subscriptions'].get('subscription', []):
            return user_subscriptions
        else:
            subscriptions = get_subscriptions_response['subscriptions']['subscription']
            # Add only those subscriptions belonging to the user of interest to user subscriptions.
            user_subscriptions.extend([subscription for subscription in subscriptions if subscription['user']['name'] == user_name])
            page_number += 1
            items_returned += page_size
            # Determine whether all subscriptions have been retrieved. 
            if items_returned >= int(get_subscriptions_response['pagination']['totalAvailable']):
                request_complete = True
    
    # Sign out of Tableau Server or Tableau Cloud instance.
    sign_out_url = f'{base_server_url}/api/3.24/auth/signout'
    sign_out_request = requests.post(sign_out_url, headers=headers, verify=False)

    return user_subscriptions

def mirror_subscriptions(
        base_server_url: str, instance_type: str, site_id: str, token_name: str,
        token_value: str, source_user_subscriptions: list[dict], target_user_item: tsc.UserItem
) -> None:
    """
    Mirrors the source user's subscriptions by creating identical subscriptions for the target user.

    Args:
        base_server_url (str): The base URL portion of the full Tableau Server or Tableau Cloud instance URL input.
        instance_type (str): Tableau Server or Tableau Cloud.
        site_id (str): The site ID value correspond the the Tableau Server or Tableau Cloud instance.
        token_name (str): The name of the personal access token configured.
        token_value (str): The secret value corresponding to the personal access token configured.
        source_user_subscriptions (list): A list containing the source user's subscriptions.
        target_user_item (tsc.UserItem): The user for which subscriptions will be created for in the process of
            mirroring the source user's subscriptions.

    Returns:
        None
    """
    # Configure progress bar.
    progress_text = 'Mirroring content...'
    progress_bar = streamlit.progress(value=0, text=progress_text)
    total_subscriptions = len(source_user_subscriptions)
    subscriptions_remaining = total_subscriptions
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
    sign_in_request = requests.post(sign_in_url, json=payload,headers=headers, verify=False)
    # Convert response to dictionary to extract the token and site ID for the subsequent subscription request.
    sign_in_response = json.loads(sign_in_request.content)
    token = sign_in_response['credentials']['token']
    site_luid = sign_in_response['credentials']['site']['id']
    headers['X-tableau-auth'] = token
    # For each source user subscription, create an identical subscription for the target user.
    for subscription in source_user_subscriptions:
        if instance_type == 'Tableau Cloud':
            new_subscription = {'subscription': subscription, 'schedule': subscription.pop('schedule')}
            new_subscription['subscription']['user'] = {'id': target_user_item.id}
        else:
            new_subscription = {'subscription': subscription}
            # A new subscription LUID will be generated upon subscription creation.
            del new_subscription['subscription']['id']
            new_subscription['subscription']['schedule'] = {'id': subscription['schedule']['id']}
            new_subscription['subscription']['user'] = {'id': target_user_item.id}
        create_new_subscription_url = f'{base_server_url}/api/3.24/sites/{site_luid}/subscriptions'
        create_new_subscription_request = requests.post(create_new_subscription_url, json=new_subscription, headers=headers, verify=False)
        create_new_subscription_response = json.loads(create_new_subscription_request.content)
        subscriptions_remaining -= 1
        progress_bar.progress(
            1 - (subscriptions_remaining / total_subscriptions),
            text=f'{round((1 - (subscriptions_remaining / total_subscriptions)) * 100)}% complete'
        )

    # Sign out of Tableau Server or Tableau Cloud instance.
    sign_out_url = f'{base_server_url}/api/3.24/auth/signout'
    sign_out_request = requests.post(sign_out_url, headers=headers, verify=False)

    # Clear the progress bar after flow restoration process is complete.
    time.sleep(1)
    progress_bar.empty()
    return None

def display_subscriptions(target_user_subscriptions: list[dict]) -> None:
    """
    Display the target user's subscriptions.

    Subscriptions for workbooks and views are displayed in individual tabs.

    Args:
    target_user_subscriptions (list[dict]): A list containing the target user's subscriptions.

    Returns:
        None
    """
    # Content info associated with the Content ID is needed to be added.
    subscription_types = set(sorted([subscription['content']['type'].upper() for subscription in target_user_subscriptions]))
    subscription_tabs = streamlit.tabs(tabs=subscription_types.copy())
    subscription_data = pd.json_normalize(target_user_subscriptions)
    subscription_data = (
        subscription_data
        .assign(**({'message': None} if 'message' not in subscription_data.columns else {}))
        .rename(
            columns={
                'id': 'Subscription ID',
                'subject': 'Subject',
                'attachImage': 'Attach Image',
                'attachPdf': 'Attach PDF',
                'suspended': 'Suspended',
                'content.id': 'Content ID',
                'content.type': 'Content Type',
                'content.sendIfViewEmpty': 'Send If Empty',
                'user.id': 'User ID',
                'message': 'Message'
            }
        )
    )
    for subscription_tab, subscription_type in zip(subscription_tabs, subscription_types):
        with subscription_tab:
            type_specific_subscription_data = (
                subscription_data
                .loc[
                    subscription_data['Content Type'].str.upper() == subscription_type,
                    [
                        'Subscription ID', 'User ID', 'Subject', 'Message', 'Content ID',
                        'Content Type', 'Attach Image', 'Attach PDF', 'Send If Empty', 'Suspended'
                    ]
                ]
            )
            streamlit.dataframe(data=type_specific_subscription_data, hide_index=True)
    return None

def extract_site_id(full_server_url) -> str | None:
    """
    Given a full server URL, returns the site ID.

    Args:
        full_server_url: The full server URL of the Tableau Server or Tableau Cloud instance.
    
    Returns:
        Site ID (str): The site ID portion of the full server URL.
    """
    match = re.search(r'/site/([^/#]+)', full_server_url)
    return match.group(1) if match else None

def extract_base_server_url(full_server_url) -> str:
    """
    Given a full server URL, returns the base URL.

    Args:
        full_server_url: The full server URL of the Tableau Server or Tableau Cloud instance.
    
    Returns:
        base url (str): The base URL portion of the full server URL input.
    """
    match = re.match(r'(https?://[^/]+)', full_server_url)
    return match.group(1) if match else None

def is_button_enabled() -> bool:
    """
    Ensures the user has provided values for all required input fields.

    Returns:
        bool: True if all required inputs are populated, False otherwise.
    """
    required_keys = [
        'FULL_SERVER_URL', 'BASE_SERVER_URL', 'INSTANCE_TYPE', 'TOKEN_NAME',
        'TOKEN_VALUE', 'SOURCE_USER', 'TARGET_USER'
    ]
    return all(streamlit.session_state[key] for key in required_keys)

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
if 'SOURCE_USER' not in streamlit.session_state:
    streamlit.session_state['SOURCE_USER'] = None
if 'TARGET_USER' not in streamlit.session_state:
    streamlit.session_state['TARGET_USER'] = None
if 'button_enabled' not in streamlit.session_state:
    streamlit.session_state['button_enabled'] = False

# Configure browser page.
streamlit.set_page_config(
    page_title="Content Mirror",
    page_icon="🪞",
)
# Add title.
streamlit.title(
    body='Content Mirror',
    help=(
        "This utility allows favorite menus and subscriptions to be copied from one user to another. "
        "User onboarding is a great usecase for the content mirror as it quickly creates favorites menus "
        "and subscriptions that mirror another user's."
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
        on_change=is_button_enabled
    )
    # Extract base URL from the full server URL provided by the user.
    if streamlit.session_state['FULL_SERVER_URL']:
        streamlit.session_state['BASE_SERVER_URL'] = extract_base_server_url(streamlit.session_state['FULL_SERVER_URL'])

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
            on_change=is_button_enabled
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
            on_change=is_button_enabled
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
            on_change=is_button_enabled
        )

# Configure user-input fields for the settings section of the UI.
settings_container = streamlit.container(border=True)
with settings_container:
    streamlit.subheader(body='Settings', anchor=False, divider='grey')
    source_user, target_user = streamlit.columns(2)
    with source_user:
        streamlit.session_state['SOURCE_USER'] = streamlit.text_input(
            label='Source user',
            value='',
            placeholder="Enter source user's user ID.",
            help=(
                """
                Enter the user ID of the user containing the favorites and/or subscriptions you would like to copy and apply
                to the target user.
                """
            ),
            on_change=is_button_enabled
        )
    with target_user:
        streamlit.session_state['TARGET_USER'] = streamlit.text_input(
            label='Target user',
            value='',
            placeholder="Enter the target user's user ID.",
            help=(
                """
                Enter the user ID of the target user for which you would like to copy the pre-existing user's favorites to.
                Only those favorites corresponding to content items (e.g., workbooks, data sources, flows, etc.) the user
                has access to can be copied.
                """
            ),
            on_change=is_button_enabled
        )

# Enable / disable button based on specific conditions.
streamlit.session_state['button_enabled'] = is_button_enabled()
mirror_favorites_button, mirror_subscriptions_button = streamlit.columns(2)
with mirror_favorites_button:
    mirror_favorites_button = streamlit.button(
        label='Mirror favorites',
        icon='💖',
        disabled=not streamlit.session_state['button_enabled']
    )
with mirror_subscriptions_button:
    mirror_subscriptions_button = streamlit.button(
        'Mirror subscriptions',
        icon='📰',
        disabled=not streamlit.session_state['button_enabled']
    )

# Mirror source user's favorites for target user.
if is_button_enabled() and mirror_favorites_button:
    TABLEAU_AUTHENTICATION = tsc.PersonalAccessTokenAuth(
        token_name=streamlit.session_state['TOKEN_NAME'],
        personal_access_token=streamlit.session_state['TOKEN_VALUE'],
        site_id=streamlit.session_state['SITE_ID']
    )
    SERVER = tsc.Server(streamlit.session_state['BASE_SERVER_URL'], use_server_version=True, http_options={'verify': False})
    access_verified = verify_access(SERVER, TABLEAU_AUTHENTICATION)
    with streamlit.status(label='Mirroring favorites...', expanded=True, state='running',) as status:
        streamlit.write('Verifying source user and target user exist...')
        source_user = valid_user(SERVER, TABLEAU_AUTHENTICATION, streamlit.session_state['SOURCE_USER'], 'SOURCE')
        target_user = valid_user(SERVER, TABLEAU_AUTHENTICATION, streamlit.session_state['TARGET_USER'], 'TARGET')
        if source_user and target_user:
            streamlit.write("Retrieving source user's favorites...")
            source_user_favorites = get_favorites(SERVER, TABLEAU_AUTHENTICATION, streamlit.session_state['SOURCE_USER'])
            if source_user_favorites:
                streamlit.write("Creating favorites for target user...")
                mirror_favorites(SERVER, TABLEAU_AUTHENTICATION, source_user_favorites, target_user)
                streamlit.write("Retrieving target user's favorites...")
                target_user_favorites = get_favorites(SERVER, TABLEAU_AUTHENTICATION, streamlit.session_state['TARGET_USER'])
                streamlit.write("Building report...")
                display_favorites(SERVER, TABLEAU_AUTHENTICATION, target_user, target_user_favorites)
                status.update(label="Mirroring process complete!", expanded=True, state="complete")
            else:
                status.update(label="The source user does not have any favorites to mirror.", expanded=False, state="error")
        else:
            status.update(label="Unable to verify the existence of the source and / or target user.", expanded=False, state="error")

# Mirror source user's subscriptions for target user.
if is_button_enabled() and mirror_subscriptions_button:
    TABLEAU_AUTHENTICATION = tsc.PersonalAccessTokenAuth(
        token_name=streamlit.session_state['TOKEN_NAME'],
        personal_access_token=streamlit.session_state['TOKEN_VALUE'],
        site_id=streamlit.session_state['SITE_ID']
    )
    SERVER = tsc.Server(streamlit.session_state['BASE_SERVER_URL'], use_server_version=True, http_options={'verify': False})
    access_verified = verify_access(SERVER, TABLEAU_AUTHENTICATION)
    with streamlit.status(label='Mirroring subscriptions...', expanded=True, state='running',) as status:
        streamlit.write('Verifying source user and target user exist...')
        source_user = valid_user(SERVER, TABLEAU_AUTHENTICATION, streamlit.session_state['SOURCE_USER'], 'SOURCE')
        target_user = valid_user(SERVER, TABLEAU_AUTHENTICATION, streamlit.session_state['TARGET_USER'], 'TARGET')
        if source_user and target_user:
            streamlit.write("Retrieving source user's subscriptions...")
            source_user_subscriptions = get_subscriptions(
                streamlit.session_state['BASE_SERVER_URL'],
                streamlit.session_state['SITE_ID'],
                streamlit.session_state['TOKEN_NAME'],
                streamlit.session_state['TOKEN_VALUE'],
                streamlit.session_state['SOURCE_USER']
            )
            if source_user_subscriptions:
                streamlit.write("Creating subscriptions for target user...")
                mirror_subscriptions(
                    streamlit.session_state['BASE_SERVER_URL'],
                    streamlit.session_state['INSTANCE_TYPE'],
                    streamlit.session_state['SITE_ID'],
                    streamlit.session_state['TOKEN_NAME'],
                    streamlit.session_state['TOKEN_VALUE'],
                    source_user_subscriptions,
                    target_user
                )
                streamlit.write("Retrieving target user's subscriptions...")
                target_user_subscriptions = get_subscriptions(
                    streamlit.session_state['BASE_SERVER_URL'],
                    streamlit.session_state['SITE_ID'],
                    streamlit.session_state['TOKEN_NAME'],
                    streamlit.session_state['TOKEN_VALUE'],
                    streamlit.session_state['TARGET_USER']
                )
                streamlit.write("Building report...")
                display_subscriptions(target_user_subscriptions)
                status.update(label="Mirroring process complete!", expanded=True, state="complete")
            else:
                status.update(label="The source user does not have any subscriptions to mirror.", expanded=False, state="error")
        else:
            status.update(label="Unable to verify the existence of the source and / or target user.", expanded=False, state="error")