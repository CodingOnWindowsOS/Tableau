from datetime import datetime, timezone
import pathlib

import keyring
import pandas as pd
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
        # Gather all workbooks.
        workbooks = [workbook for workbook in tsc.Pager(server.workbooks)]
        # Gather all workbook views (i.e., sheets).
        views = [view for view in tsc.Pager(server.views, usage=True)]
        # Gather all users.
        users = [user for user in tsc.Pager(server.users)]

    # Create a dataframe containing workbook information.
    workbook_info = pd.DataFrame(
        [
            {
                'Workbook ID': workbook.id,
                'Workbook Owner ID': workbook.owner_id,
                'Workbook Name': workbook.name,
                'Workbook Created At': workbook.created_at,
                'Workbook Updated At': workbook.updated_at,
                'Workbook Content URL': workbook.webpage_url,
                'Workbook Project ID': workbook.project_id,
                'Workbook Project Name': workbook.project_name
            }
            for workbook in workbooks
        ]
        
    )

    # Create a dataframe containing the number of views per workbook.
    total_views_per_workbook = (
        pd.DataFrame([view.__dict__ for view in views])
        .groupby('_workbook_id')['_total_views']
        .sum()
        .reset_index()
        .rename(
            columns={
                '_workbook_id': 'Workbook ID',
                '_total_views': 'Workbook Total Views'
            }
        )
    )

    # Create a dataframe containing user information.
    user_info = pd.DataFrame(
        [
            {
                'User ID': user.id,
                'User Display Name': user.fullname,
                'User Email Address': user.email,
                'User Site Role': user.site_role,
            }
            for user in users
        ]
    )

    # Create a workbooks report by merging workbook info, view info, and user info dataframes.
    workbooks_report = (
        workbook_info
        .merge(
            right=total_views_per_workbook,
            how='inner',
            on='Workbook ID'
        )
        .merge(
            right=user_info,
            how='inner',
            left_on='Workbook Owner ID',
            right_on='User ID'
        )
        .drop(columns=['User ID'])
        .rename(
            columns={
                'User Display Name': 'Workbook Owner Name',
                'User Email Address': 'Workbook Owner Email Address',
                'User Site Role': 'Workbook Owner Site Role'
            }
        )
        .reindex(
            columns=[
                'Workbook ID', 'Workbook Name',
                'Workbook Total Views', 'Workbook Created At',
                'Workbook Updated At', 'Workbook Content URL',
                'Workbook Project ID', 'Workbook Project Name',
                'Workbook Owner ID', 'Workbook Owner Name',
                'Workbook Owner Email Address', 'Workbook Owner Site Role'
            ]
        )
    )

    # Remove the timezone information from each value in order to write to excel file.
    workbooks_report['Workbook Created At'] = workbooks_report['Workbook Created At'].dt.tz_localize(None)
    workbooks_report['Workbook Updated At'] = workbooks_report['Workbook Updated At'].dt.tz_localize(None)
    
    # Create and write workbooks report dataframe to specified file path.
    write_path = pathlib.Path(
        f'C:/Users/Chris/OneDrive/Desktop/social_media_content/youtube/tableau_server_client/tutorial_8/workbooks_report_'\
        f'{datetime.now(tz=timezone.utc).strftime("%Y%m%d%H%M%S")}.xlsx'
    )

    with pd.ExcelWriter(write_path) as writer:
        workbooks_report.to_excel(writer, sheet_name='Workbooks', index=False)

if __name__ == '__main__':
    main()
