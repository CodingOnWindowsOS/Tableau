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
        # Create a group filter for the request to add a user.
        request_options = tsc.RequestOptions()
        request_options.filter.add(
            tsc.Filter(
                tsc.RequestOptions.Field.Name,
                tsc.RequestOptions.Operator.Equals,
                'North America Sales Team'
            )
        )

        # Retrieve the specific group object requiring updates, if it exists.
        if server.groups.get(request_options)[0]:
            group = server.groups.get(request_options)[0][0]
            # Add all users currently existing on the Tableau Server or Tableau Cloud instance to this group.
            users = [user for user in tsc.Pager(server.users)]
            for user in users:
                try:
                    server.groups.add_user(group_item=group, user_id=user.id)
                except:
                    print(f'Unable to add {user.name} to {group.name}.')
                else:
                    print(f'Added {user.name} to {group.name}.')
        else:
            print('Group not found.')

if __name__ == '__main__':
    main()