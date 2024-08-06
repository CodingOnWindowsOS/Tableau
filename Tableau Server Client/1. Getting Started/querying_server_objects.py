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
        # Create a dataframe containing data source information.
        data_source_info = pd.DataFrame(
            {
                'Data Source ID': [data_source.id for data_source in data_sources],
                'Data Source Owner ID': [data_source.owner_id for data_source in data_sources],
                'Data Source Name': [data_source.name for data_source in data_sources],
                'Data Source Project ID': [data_source.project_id for data_source in data_sources],
                'Data Source Project Name': [data_source.project_name for data_source in data_sources],
                'Data Source Created At': [data_source.created_at for data_source in data_sources],
                'Data Source Updated At': [data_source.updated_at for data_source in data_sources]           
            }
        )
        # Display data source info.
        print(data_source_info)

if __name__ == '__main__':
    main()
