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
        # Gather all workbooks.
        workbooks = [workbook for workbook in tsc.Pager(server.workbooks)]
        # Gather all workbook views (i.e., sheets).
        views = [view for view in tsc.Pager(server.views, usage=True)]
        # Gather all users.
        users = [user for user in tsc.Pager(server.users)]

    # Create a dataframe containing workbook information.
    workbook_info = pd.DataFrame(
        {
            'Workbook ID': [workbook.id for workbook in workbooks],
            'Workbook Owner ID': [workbook.owner_id for workbook in workbooks],
            'Workbook Name': [workbook.name for workbook in workbooks],
            'Workbook Created At': [workbook.created_at for workbook in workbooks],
            'Workbook Updated At': [workbook.created_at for workbook in workbooks],
            'Workbook Content URL': [workbook.webpage_url for workbook in workbooks],
            'Workbook Project ID': [workbook.project_id for workbook in workbooks],
            'Workbook Project Name': [workbook.project_name for workbook in workbooks]
        }
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
        {
            'User ID': [user.id for user in users],
            'User Display Name': [user.fullname for user in users],
            'User Email Address': [user.email for user in users],
            'User Site Role': [user.site_role for user in users]
        }
    )

    # Create a workbooks report by merging workbook info and user info dataframes.
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
        f'C:/Users/Chris/Desktop/social_media_content/youtube/tableau_server_client/tutorial_8/workbooks_report_'\
        f'{datetime.now(tz=timezone.utc).strftime("%Y%m%d%H%M%S")}.xlsx'
    )

    with pd.ExcelWriter(write_path) as writer:
        workbooks_report.to_excel(writer, sheet_name='Workbooks', index=False)

if __name__ == '__main__':
    main() 