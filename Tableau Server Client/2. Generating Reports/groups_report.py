from datetime import datetime, timezone
import keyring
import pandas as pd
import pathlib
import tableauserverclient as tsc

def main():
    # Setup
    # Store token name, token value, and site ID in variables.
    token_name = 'TSM'
    token_value = keyring.get_password('Tableau Server Management', 'TSM')
    site_id = 'sqlshortreads'
    # Create authentication object using the token and site ID details.
    tableau_auth = tsc.PersonalAccessTokenAuth(token_name=token_name, personal_access_token=token_value, site_id=site_id)
    # Create a tableau server client object using specified server URL.
    server = tsc.Server('https://10ax.online.tableau.com')
    # Disable certificate verification. The next line of code may be required due to certificate issues.
    # server.add_http_options({'verify': False})

    # Sign-in to server.
    with server.auth.sign_in(tableau_auth):
        # Ensure the most recent Tableau REST API version is used.
        server.use_highest_version()
        # Gather all groups.
        groups = [group for group in tsc.Pager(server.groups)]
        # Populate the user info for each user within each group.
        for group in groups:
            server.groups.populate_users(group)
        # Create a dataframe containing group information.
        group_info = pd.DataFrame(
            {
                'Group ID': [group.id for group in groups],
                'Group Name': [group.name for group in groups],
                'Group Domain': [group.domain_name for group in groups],
                'Users': [[user.id for user in group.users] for group in groups]
            }
        )
        
        # Transform dataframe to be display one row per group per user.
        group_info = group_info.explode(column='Users')
        
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

    # Create a groups report by merging project info and user info dataframes.
    groups_report = (
        group_info
        .merge(
            right=user_info,
            how='left',
            left_on='Users',
            right_on='User ID'
        )
        .drop(columns=['User ID'])
    )
        
    # Create and write groups report dataframe to specified file path.
    write_path = pathlib.Path(
        f'C:/Users/Chris/Desktop/social_media_content/youtube/tableau_server_client/tutorial_5/groups_report_'\
        f'{datetime.now(tz=timezone.utc).strftime("%Y%m%d%H%M%S")}.xlsx'
    )

    with pd.ExcelWriter(write_path) as writer:
        groups_report.to_excel(writer, sheet_name='Groups', index=False)

if __name__ == '__main__':
    main()
