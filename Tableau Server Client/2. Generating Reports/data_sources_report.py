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
        # Gather all data sources.
        data_sources = [data_source for data_source in tsc.Pager(server.datasources)]
        # Gather all users.
        users = [user for user in tsc.Pager(server.users)]

    # Create a dataframe containing data source information.
    data_source_info = pd.DataFrame(
        {
            'Data Source ID': [data_source.id for data_source in data_sources],
            'Data Source Owner ID': [data_source.owner_id for data_source in data_sources],
            'Data Source Name': [data_source.name for data_source in data_sources],
            'Data Source Type': [data_source.datasource_type for data_source in data_sources],
            'Data Source Created At': [data_source.created_at for data_source in data_sources],
            'Data Source Updated At': [data_source.updated_at for data_source in data_sources],
            'Data Source Project ID': [data_source.project_id for data_source in data_sources],
            'Data Source Project Name': [data_source.project_name for data_source in data_sources]
        }
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

    # Create a data sources report by merging data source info and user info dataframes.
    data_sources_report = (
        data_source_info
        .merge(
            right=user_info,
            how='inner',
            left_on='Data Source Owner ID',
            right_on='User ID',
        )
        .drop(columns=['User ID'])
        .rename(
            columns={
                'User Display Name': 'Data Source Owner Name',
                'User Email Address': 'Data Source Owner Email Address',
                'User Site Role': 'Data Source Owner Site Role'
            }
        )
        .reindex(
            columns=[
                'Data Source ID', 'Data Source Name',
                'Data Source Type', 'Data Source Created At',
                'Data Source Updated At', 'Data Source Project ID',
                'Data Source Project Name', 'Data Source Owner ID',
                'Data Source Owner Name', 'Data Source Owner Email Address',
                'Data Source Owner Site Role'
            ]
        )
    )

    # Remove the timezone information from each value in order to write to excel file.
    data_sources_report['Data Source Created At'] = data_sources_report['Data Source Created At'].dt.tz_localize(None)
    data_sources_report['Data Source Updated At'] = data_sources_report['Data Source Updated At'].dt.tz_localize(None)

    # Create and write data sources report dataframe to specified file path.
    write_path = pathlib.Path(
        f'C:/Users/Chris/Desktop/social_media_content/youtube/tableau_server_client/tutorial_7/data_sources_report_'\
        f'{datetime.now(tz=timezone.utc).strftime("%Y%m%d%H%M%S")}.xlsx'
    )

    with pd.ExcelWriter(write_path) as writer:
        data_sources_report.to_excel(writer, sheet_name='Data Sources', index=False)

if __name__ == '__main__':
    main() 
