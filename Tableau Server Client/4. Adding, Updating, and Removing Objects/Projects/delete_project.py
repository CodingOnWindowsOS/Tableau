import keyring
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
        # Create a project filter for the deletion request.
        project = server.projects.filter(name='Salesforce')
        
        # Retrieve the specific project object requiring deletion, if it exists.
        if project:
            project = project[0]
            # Delete the project from the Tableau Server or Tableau Cloud instance.
            try:
                server.projects.delete(project_id=project.id)
            except:
                print(f'Unable to delete {project.name}.')
            else:
                print(f'{project.name} successfully deleted from the server.')
        else:
            print('Project not found.')

if __name__ == '__main__':
    main()