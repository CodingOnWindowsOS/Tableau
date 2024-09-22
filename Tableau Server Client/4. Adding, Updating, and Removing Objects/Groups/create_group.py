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
        # Configure new group. Set minimum site role and license mode based on scenario.
        new_group = tsc.GroupItem(name='North America Sales Team')
        new_group.minimum_site_role = None
        new_group.license_mode = None

        # Create the group on Tableau Server or Tableau Cloud instance.
        try:
            server.groups.create(group_item=new_group)
        except:
            print(f'Unable to create {new_group.name}.')
        else:
            print(f'{new_group.name} successfully created.')

if __name__ == '__main__':
    main()