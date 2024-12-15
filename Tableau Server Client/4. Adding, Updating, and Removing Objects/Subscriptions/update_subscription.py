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
        # Retrieve the user requiring an update to their subscription.
        user = server.users.filter(name='cmp160130@gmail.com')
        # Retrieve the subscription's content (e.g., workbook, view)
        target = server.views.filter(name='North America Sales')
        # Retrieve the subscription requiring an update.
        subscription = [
            subscription for subscription in tsc.Pager(server.subscriptions)
            if subscription.target.id == target[0].id and subscription.user_id == user[0].id
        ]
        subscription = subscription[0]
        # Update the subscription's schedule.
        subscription.schedule_id = '2c981d53-4326-4acc-b4e0-65081c475034'
        try:
            server.subscriptions.update(subscription)
        except:
            print(f'Unable to update subscription for {subscription.user_id} with a target ID of {subscription.target.id}')
        else:
            print(f'Sucessfully updated subscription for {subscription.user_id} with a target ID of {subscription.target.id}')

if __name__ == '__main__':
    main()