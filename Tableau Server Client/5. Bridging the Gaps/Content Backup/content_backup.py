import keyring
import tableauserverclient as tsc
from pathlib import Path

# Specify path to download content to.
DOWNLOAD_TO_PATH = Path('C:/Users/Chris/Desktop/social_media_content/youtube/tableau_server_client/tutorial_25/content_backup')

def download_content(
        server: tsc.Server,
        tableau_authentication: tsc.PersonalAccessTokenAuth,
        download_to_path: Path,
        content_type: str = 'all'
) -> None:
    """
    Downloads the user-specified content types from a Tableau Server or Tableau Cloud instance to the path provided.

    Args:
        server (tsc.Server): The connected Tableau Server or Cloud instance.
        tableau_authentication (tsc.PersonalAccessTokenAuth): The authentication mechanism for connecting
            to the Tableau Server or Cloud instance.
        download_to_path (Path): The path to download the content to.
        content_type (str): The type of content (e.g., workbooks, data sources, flows, all) to download.
    """
    with server.auth.sign_in(tableau_authentication):
        content_types = ['data sources', 'flows', 'workbooks', 'all']
        if content_type not in content_types:
            raise ValueError(f"Invalid content type '{content_type}'. Expected one of: {content_types}")

        if content_type == 'all':
            data_sources = [data_source for data_source in tsc.Pager(server.datasources)]
            for data_source in data_sources:
                server.datasources.download(datasource_id=data_source.id, filepath=DOWNLOAD_TO_PATH, include_extract=True)

            flows = [flow for flow in tsc.Pager(server.flows)]
            for flow in flows:
                server.flows.download(flow_id=flow.id, filepath=DOWNLOAD_TO_PATH)

            workbooks = [workbook for workbook in tsc.Pager(server.workbooks)]
            for workbook in workbooks:
                server.workbooks.download(workbook_id=workbook.id, filepath=DOWNLOAD_TO_PATH, include_extract=True)
            return None
        
        if content_type == 'data sources':
            data_sources = [data_source for data_source in tsc.Pager(server.datasources)]
            for data_source in data_sources:
                server.datasources.download(datasource_id=data_source.id, filepath=DOWNLOAD_TO_PATH, include_extract=True)
            return None
        
        if content_type == 'flows':
            flows = [flow for flow in tsc.Pager(server.flows)]
            for flow in flows:
                server.flows.download(flow_id=flow.id, filepath=DOWNLOAD_TO_PATH)
            return None
        
        if content_type == 'workbooks':
            workbooks = [workbook for workbook in tsc.Pager(server.workbooks)]
            for workbook in workbooks:
                server.workbooks.download(workbook_id=workbook.id, filepath=DOWNLOAD_TO_PATH, include_extract=True)
            return None
        
def main():
    # Setup
    # Store token name, token value, and site ID in variables.
    TOKEN_NAME = 'TSM'
    TOKEN_VALUE = keyring.get_password('Tableau Server Management', 'TSM')
    SITE_ID = 'sqlshortreads'
    # Create authentication object using the token and site ID details.
    TABLEAU_AUTHENTICATION = tsc.PersonalAccessTokenAuth(token_name=TOKEN_NAME, personal_access_token=TOKEN_VALUE, site_id=SITE_ID)
    # Create a tableau server client object using specified server URL.
    SERVER = tsc.Server('https://10ax.online.tableau.com', use_server_version=True)
    # Disable certificate verification. The next line of code may be required due to certificate issues.
    # server.add_http_options({'verify': False})

    # Download all content or that indicated by the content type.
    download_content(server=SERVER, tableau_authentication=TABLEAU_AUTHENTICATION, download_to_path=DOWNLOAD_TO_PATH, content_type='data sources')

if __name__ == '__main__':
    main()