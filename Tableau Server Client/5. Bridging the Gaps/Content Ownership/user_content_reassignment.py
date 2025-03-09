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
    # Read in user content mapping and create lists of each user type.
    user_content_mapping = pd.read_excel(r'C:\Users\Chris\OneDrive\Desktop\social_media_content\youtube\tableau_server_client\tutorial_26\user_content_mapping.xlsx')
    from_users = user_content_mapping['FROM_USER'].to_list()
    to_users = user_content_mapping['TO_USER'].to_list()

    # Authenticate and sign-in to the Tableau Server or Tableau Cloud instance.
    with SERVER.auth.sign_in(TABLEAU_AUTHENTICATION):
        # Iterate through each row containing the respective user content mapping.
        for from_user, to_user in zip(from_users, to_users):
            # Retrieve data sources and workbooks associated with the 'from_user.'
            from_user = SERVER.users.filter(name=from_user)[0]
            to_user = SERVER.users.filter(name=to_user)[0]
            data_sources = [data_source for data_source in tsc.Pager(SERVER.datasources) if data_source.owner_id == from_user.id]
            workbooks = [workbook for workbook in tsc.Pager(SERVER.workbooks) if workbook.owner_id == from_user.id]
            # Assign data sources and workbooks owned by 'from_user' to 'to_user.'
            if data_sources:
                for data_source in data_sources:
                    data_source.owner_id = to_user.id
                    SERVER.datasources.update(data_source_item=data_source)

            if workbooks:
                for workbook in workbooks:
                    workbook.owner_id = to_user.id
                    SERVER.workbooks.update(workbook_item=workbook)

if __name__ == '__main__':
    main()
