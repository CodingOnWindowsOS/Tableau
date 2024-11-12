import keyring
from pathlib import Path
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
        # Create a workbook filter for the deletion request.
        workbook = server.workbooks.filter(name='Europe Sales: Open Pipeline')
        
        # Retrieve the specific workbook object requiring deletion, if it exists.
        if workbook:
            workbook = workbook[0]
            # Delete the workbook from the Tableau Server or Tableau Cloud instance.
            try:
                server.workbooks.delete(workbook_id=workbook.id)
            except:
                print(f'Unable to delete {workbook.name}.')
            else:
                print(f'{workbook.name} successfully deleted from the server.')
        else:
            print('Workbook not found.')

if __name__ == '__main__':
    main()