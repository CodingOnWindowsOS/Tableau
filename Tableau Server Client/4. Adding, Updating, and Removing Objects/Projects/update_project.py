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
        # Create a project filter for the update request.
        project = server.projects.filter(name='Salesforce')
        
        # Retrieve the specific project object requiring updates, if it exists.
        if project:
            project = project[0]
            # Update the project's content permissions model type.
            project.content_permissions = 'ManagedByOwner'
            # Update the project's content permissions model type on Tableau Server or Tableau Cloud instance.
            try:
                server.projects.update(project_item=project)
            except:
                print(f'Unable to update the content permissions model type to {project.content_permissions}.')
            else:
                print(f'The content permissions model type was successfully updated to {project.content_permissions} for {project.name}.')
        else:
            print('Project not found.')

if __name__ == '__main__':
    main()