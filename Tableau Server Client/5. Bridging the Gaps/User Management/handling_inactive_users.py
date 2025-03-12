from datetime import datetime, timezone
import keyring
import pandas as pd
import tableauserverclient as tsc

def main():
    # Setup
    # Store token name, token value, and site ID in variables.
    TOKEN_NAME = 'TSM'
    TOKEN_VALUE = keyring.get_password('Tableau Server Management', 'TSM')
    SITE_ID = 'sqlshortreads'
    # Create authentication object using the token and site ID details.
    TABLEAU_AUTHENTICATION = tsc.PersonalAccessTokenAuth(token_name=TOKEN_NAME, personal_access_token=TOKEN_VALUE, site_id=SITE_ID)
    # Create a tableau server client object using specified server URL.
    SERVER = tsc.Server('https://10ax.online.tableau.com', use_server_version=True, http_options={'verify': False})
    # Specify the number of days of inactivity a user is permitted before being considered an inactive user.
    IS_ACTIVE_THRESHOLD = 10

    # Authenticate and sign-in to the Tableau Server or Tableau Cloud instance.
    with SERVER.auth.sign_in(TABLEAU_AUTHENTICATION):
        users = [user for user in tsc.Pager(SERVER.users) if (datetime.now(timezone.utc) - user.last_login).days > IS_ACTIVE_THRESHOLD]
        # Create a dataframe containing inactive users.
        inactive_users = pd.DataFrame(
            [
                (user.id, user.fullname, user.email, user.site_role, user.last_login, (datetime.now(timezone.utc) - user.last_login).days)
                for user in users
            ],
            columns=['ID', 'Full Name', 'Email Address', 'Site Role', 'Last Login (UTC)', 'Days Since Last Login']
        )

        # Remove the timezone so that the dataframe can be written to an excel file.
        inactive_users['Last Login (UTC)'] = inactive_users['Last Login (UTC)'].dt.tz_localize(None)
        # Write the inactive users dataframe to an excel file.
        inactive_users.to_excel(
            excel_writer=r'C:\Users\Chris\OneDrive\Desktop\social_media_content\youtube\tableau_server_client\tutorial_27\inactive_users.xlsx',
            index=False
        )
        # Unlicense each inactive user identified.
        for user in users:
            user.site_role = 'Unlicensed'
            SERVER.users.update(user_item=user)

if __name__ == '__main__':
    main()