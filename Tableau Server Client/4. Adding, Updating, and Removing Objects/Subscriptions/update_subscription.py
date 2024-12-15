import keyring
import tableauserverclient as tsc

def main():
    # Setup
    # Store token name and token value in variables.
    token_name = 'TSM'
    token_value = keyring.get_password('Tableau Server Management', 'TSM')
    # Create authentication object using the token details.
    tableau_auth = tsc.PersonalAccessTokenAuth(token_name=token_name, personal_access_token=token_value, site_id='sqlshortreads')
    # Create a tableau server client object using specified server URL.
    server = tsc.Server('https://10ax.online.tableau.com')
    # Disable certificate verification. The next line of code may be required due to certificate issues.
    # server.add_http_options({'verify': False})

    # Authenticate with Tableau server.
    with server.auth.sign_in(tableau_auth):
        # Ensure the most recent Tableau REST API version is used.
        server.use_highest_version()
        # Retrieve the user requiring their subscriptions to be deleted.
        user = server.users.filter(name='cmp160130@gmail.com')
        # Retrieve the subscription(s) requiring deletion.
        subscriptions = [
            subscription for subscription in tsc.Pager(server.subscriptions)
            if subscription.user_id == user[0].id
        ]
        # Delete each of the user's non-flow subscriptions.
        for subscription in subscriptions:
            try:
                server.subscriptions.delete(subscription.id)
            except:
                print(f'Unable to delete subscription for {subscription.user_id} with a target ID of {subscription.target.id}')
            else:
                print(f'Sucessfully deleted subscription for {subscription.user_id} with a target ID of {subscription.target.id}')

if __name__ == '__main__':
    main()
