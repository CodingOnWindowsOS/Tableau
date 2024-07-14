from datetime import datetime, timezone
import keyring
import pandas as pd
import pathlib
import tableauserverclient as tsc

def main():
    # Setup
    # Store token name and token value in variables.
    token_name = 'TSM'
    token_value = keyring.get_password('Tableau Server Management', 'TSM')
    # Create authentication object using the token details.
    tableau_auth = tsc.PersonalAccessTokenAuth(token_name=token_name, personal_access_token=token_value, site_id='sqlshortreads')
    # Create a tableau server client object using specified server URL.
    server = tsc.Server('https://10ax.online.tableau.com')
    # Disable certificate verification. The next line of code may be required due to certificate issues.
    # server.add_http_options({'verify': False})

    # Sign-in to server.
    with server.auth.sign_in(tableau_auth):
        # Ensure the most recent Tableau REST API version is used.
        server.use_highest_version()
        # Gather all users.
        users = [user for user in tsc.Pager(server.users)]
        # Create a dataframe containing user information.
        user_info = pd.DataFrame(
            {
                'User ID': [user.id for user in users],
                'User Name': [user.name for user in users],
                'User Display Name': [user.fullname for user in users],
                'User Email Address': [user.email for user in users],
                'User Domain': [server.users.get_by_id(user.id).domain_name for user in users],
                'User Site Role': [user.site_role for user in users]
            }
        )
        
        # Gather user ID values for owners of flows, data sources, and workbooks.
        flow_owners = [flow.owner_id for flow in tsc.Pager(server.flows)]
        data_source_owners = [data_source.owner_id for data_source in tsc.Pager(server.datasources)]
        workbook_owners = [workbook.owner_id for workbook in tsc.Pager(server.workbooks)]

    # Get unique ID values across each list and consolidate those values into one list.
    flow_owners = set(flow_owners)
    data_source_owners = set(data_source_owners)
    workbook_owners = set(workbook_owners)
    flow_owners.update(data_source_owners)
    flow_owners.update(workbook_owners)
    owners = set(flow_owners)

    # Create a user report based on the user info dataframe.
    users_report = (
        user_info
        .assign(
            is_owner=user_info['User ID'].isin(owners)
        )
        .rename(columns={'is_owner': 'Content Owner'})
        .sort_values(by='Content Owner', ascending=False)
    )

    # Create and write users report dataframe to specified file path.
    write_path = pathlib.Path(
        f'C:/Users/Chris/Desktop/social_media_content/youtube/tableau_server_client/tutorial_4/users_report_'\
        f'{datetime.now(tz=timezone.utc).strftime("%Y%m%d%H%M%S")}.xlsx'
    )

    with pd.ExcelWriter(write_path) as writer:
        users_report.to_excel(writer, sheet_name='Users', index=False)

if __name__ == '__main__':
    main()
