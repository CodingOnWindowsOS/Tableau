from datetime import datetime, timezone
import keyring
import pandas as pd
import pathlib
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
        # Gather all subscriptions.
        subscriptions = [subscription for subscription in tsc.Pager(server.subscriptions)]
        # Gather all workbooks.
        workbooks = [workbook for workbook in tsc.Pager(server.workbooks)]
        # Gather all workbook views (i.e., sheets).
        views = [view for view in tsc.Pager(server.views)]
        # Gather all users
        users = [user for user in tsc.Pager(server.users)]

    # Create a dataframe containing subscription information.
    subscription_info = pd.DataFrame(
        {
            'Subscription ID': [subscription.id for subscription in subscriptions],
            'Subscription Owner ID': [subscription.user_id for subscription in subscriptions],
            'Subscription Subject': [subscription.subject for subscription in subscriptions],
            'Subscription Content ID': [subscription.target.id for subscription in subscriptions],
            'Subscription Content Type': [subscription.target.type for subscription in subscriptions],
            'Subscription Schedule': [subscription.schedule[0].interval_item for subscription in subscriptions]
        }
    )

    # Create a dataframe containing workbook information.
    workbook_info = pd.DataFrame(
        {
            'Content ID': [workbook.id for workbook in workbooks],
            'Content Owner ID': [workbook.owner_id for workbook in workbooks],
            'Content Name': [workbook.name for workbook in workbooks],
            'Content URL': [workbook.webpage_url for workbook in workbooks]
        }
    )

    # Create a dataframe containing view information.
    view_info = pd.DataFrame(
        {
            'Content ID': [view.id for view in views],
            'Content Owner ID': [view.owner_id for view in views],
            'Content Name': [view.name for view in views],
            'Content URL': [
                server.server_address
                + '/#/site/sqlshortreads/views/'
                + view.content_url.replace('/sheets/', '/') 
                for view in views
            ]
        }
    )

    # Vertically concatenate the workbook info and view info dataframes.
    content_info = pd.concat(
        [workbook_info, view_info],
        axis=0,
        ignore_index=True
    )

    # Create a dataframe containing user information.
    user_info = pd.DataFrame(
        {
            'User ID': [user.id for user in users],
            'User Display Name': [user.fullname for user in users],
            'User Email Address': [user.email for user in users],
            'User Site Role': [user.site_role for user in users]
        }
    )

    # Create a subscriptions report by merging the subscription info, workbook info, view info, and user info dataframes.
    subscriptions_report = pd.DataFrame(
        subscription_info
        .merge(
            right=content_info,
            left_on='Subscription Content ID',
            right_on='Content ID'
        )
        .drop(columns=['Subscription Content ID'])
        .merge(
            right=user_info,
            left_on='Subscription Owner ID',
            right_on='User ID'
        )
        .drop(columns=['User ID'])
        .rename(
            columns={
                'User Display Name': 'Subscription Owner Display Name',
                'User Email Address': 'Subscription Owner Email Address',
                'User Site Role': 'Subscription Owner Site Role'
            }
        )
        .merge(
            right=user_info,
            left_on='Content Owner ID',
            right_on='User ID'       
        )
        .drop(columns=['User ID'])
        .rename(
            columns={
                'User Display Name': 'Content Owner Display Name',
                'User Email Address': 'Content Owner Email Address',
                'User Site Role': 'Content Owner Site Role'
            }
        )
        .reindex(
            columns=[
                'Subscription ID', 'Subscription Owner ID', 'Subscription Subject',
                'Subscription Schedule', 'Subscription Owner Display Name', 'Subscription Owner Email Address',
                'Subscription Owner Site Role', 'Subscription Content Type', 'Content ID',
                'Content Name', 'Content URL', 'Content Owner ID',
                'Content Owner Display Name', 'Content Owner Email Address', 'Content Owner Site Role'
            ]
        )
    )
        
    # Create and write subscriptions report dataframe to specified file path.
    write_path = pathlib.Path(
        f'C:/Users/Chris/Desktop/social_media_content/youtube/tableau_server_client/tutorial_10/subscriptions_report_'\
        f'{datetime.now(tz=timezone.utc).strftime("%Y%m%d%H%M%S")}.xlsx'
    )

    with pd.ExcelWriter(write_path) as writer:
        subscriptions_report.to_excel(writer, sheet_name='Subscriptions', index=False)

if __name__ == '__main__':
    main() 
