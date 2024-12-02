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
        # Create a filter for the project for which the flow will be published.
        # There are multiple "flows" projects, so the one with a parent project
        # name of "Europe Sales" must be identified.
        parent_project = server.projects.filter(name='Europe Sales')
        projects = server.projects.filter(name='Flows')
        project = [project for project in projects if project.parent_id == parent_project[0].id]

        # Configure the new flow.
        new_flow = tsc.FlowItem(
            name='Dynamic calendar table',
            project_id=project[0].id
        )

        # Publish the new flow to the Tableau Server or Tableau Cloud instance.
        try:
            server.flows.publish(
                flow_item=new_flow,
                file=Path('C:/Users/Chris/Desktop/social_media_content/youtube/tableau_server_client/tutorial_21/dynamic_calendar_table.tflx'),
                mode='CreateNew'
            )
        except:
            print(f'Unable to publish {new_flow.name}.')
        else:
            print(f'{new_flow.name} successfully published.')

if __name__ == '__main__':
    main()
