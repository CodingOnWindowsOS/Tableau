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
        # Retrieve the user requiring the new subscription.
        user = server.users.filter(name='cmp160130@gmail.com')
        # Retrieve the to-be subscription's content (e.g., workbook, view)
        target = server.workbooks.filter(name='North America Sales')
        # Configure the new subscription item.
        new_subscription = tsc.SubscriptionItem(
            subject='North America Sales (demo)',
            schedule_id='f3dcaf7a-9668-4eb2-8c20-2f7c21e82744',
            user_id=user[0].id,
            target=tsc.Target(target[0].id, target_type='Workbook')
        )
        # Set additional subscription attributes.
        new_subscription.message = 'Please see the attached North America Sales report for today.'
        new_subscription.attach_image = True
        new_subscription.attach_pdf = True
        new_subscription.page_orientation = tsc.PDFRequestOptions.Orientation.Portrait
        new_subscription.page_size_option = tsc.PDFRequestOptions.PageType.Letter
        new_subscription.send_if_view_empty = False
        new_subscription.suspended = False

        # Subscribe the user to the target content.
        try:
            server.subscriptions.create(subscription_item=new_subscription)
        except:
            print(f'Unable to create subscription for {user[0].name}')
        else:
            print(f'Sucessfully created subscription for {user[0].name}.')

if __name__ == '__main__':
    main()