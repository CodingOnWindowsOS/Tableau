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
        # Create a workbook filter for the update request.
        workbook = server.workbooks.filter(name='Europe Sales: Open Pipeline')
        # Create a user request filter for the new workbook owner.
        user = server.users.filter(name='soloqueuelegendsql@gmail.com')
        
        # Retrieve the specific workbook object requiring updates, if it exists.
        if workbook and user:
            workbook = workbook[0]
            user = user[0]
            # Update the workbook's owner.
            workbook.owner_id = user.id
            try:
                server.workbooks.update(workbook)
            except:
                print(f'Unable to update the owner for the {workbook.name} workbook.')
            else:
                print(f'Successfully updated the owner for the {workbook.name} workbook.')
        else:
            print(f'Workbook and/or user not found.')

if __name__ == '__main__':
    main()