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
        server.use_server_version()
        # Retrieve the user requiring the new favorite.
        user = server.users.filter(name='cmp160130@gmail.com')[0]
        # Gather various items important to users within the North America Sales Team.
        new_favorites = {
            'project': server.projects.filter(name='North America Sales')[0],
            'workbook': server.workbooks.filter(name='North America Sales')[0],
            'datasource': server.datasources.filter(name='North America Sales')[0],
            'flow': server.flows.filter(name='North America Sales (Bridge-enabled)')[0]
        }
        # Add the items to the user's favorites menu.
        for favorite_type, favorite_item in new_favorites.items():
            try:
                 server.favorites.add_favorite(user_item=user, content_type=favorite_type, item=favorite_item)
            except tsc.ServerResponseError:
                print(f"Unable to add {favorite_item.name} ({favorite_type}) to the user's favorites")
            else:
                print(f"Successfully added {favorite_item.name} ({favorite_type}) to the user's favorites.")
           
        # Verify the favorites were added by populating the user's favorites.
        server.users.populate_favorites(user)
        print(user.favorites)

if __name__ == '__main__':
    main()