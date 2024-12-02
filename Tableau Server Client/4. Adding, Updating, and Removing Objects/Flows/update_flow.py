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
        # Create a flow filter for the update request.
        flow = server.flows.filter(name='Dynamic calendar table')
        # Create a project filter for the project for which the flow will be moved to.
        # There are multiple "flows" projects, so the one with a parent project
        # name of "Europe Sales" must be identified.
        parent_project = server.projects.filter(name='Europe Sales')
        projects = server.projects.filter(name='Flows')
        project = [project for project in projects if project.parent_id == parent_project[0].id]

        # Retrieve the specific flow object requiring updates, if it exists.
        if flow and project:
            flow = flow[0]
            project = project[0]
            # Update the flow's project (location).
            flow.project_id = project.id
            try:
                server.flows.update(flow)
            except:
                print(f'Unable to update the project for the {flow.name} flow.')
            else:
                print(f'Successfully updated the project for the {flow.name} flow.')
        else:
            print(f'Flow and/or user not found.')

if __name__ == '__main__':
    main()