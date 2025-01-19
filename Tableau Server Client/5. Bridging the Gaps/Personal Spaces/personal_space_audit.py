import keyring
import tableauserverclient as tsc
import time

def main():
    # Setup
    # Store token name, token value, and site ID in variables.
    token_name = 'TSM'
    token_value = keyring.get_password('Tableau Server Management', 'TSM')
    site_id = 'sqlshortreads'
    # Create authentication object using the token and site ID details.
    tableau_auth = tsc.PersonalAccessTokenAuth(token_name=token_name, personal_access_token=token_value, site_id=site_id)
    # Create a tableau server client object using specified server URL.
    server = tsc.Server('https://10ax.online.tableau.com', use_server_version=True)
    # Disable certificate verification. The next line of code may be required due to certificate issues.
    # server.add_http_options({'verify': False})

    with server.auth.sign_in(tableau_auth):
        # Gather all personal space workbooks.
        workbooks = [
            workbook for workbook in tsc.Pager(server.workbooks)
            if workbook.project_name is None
        ]

        # Create project for the audit of personal space workbooks.
        new_project = tsc.ProjectItem(
            name='Personal Space Audit',
            description='The area for which the audit of personal space workbooks is to take place.'
        )
        server.projects.create(project_item=new_project)
        # Allow sufficient time for the new project to be indexed on server.
        time.sleep(2)
        new_project_id = server.projects.filter(name='Personal Space Audit')[0].id

        # Move each workbook to the Personal Space Audit project.
        for workbook in workbooks:
            workbook.project_id = new_project_id
            server.workbooks.update(workbook)

if __name__ == '__main__':
    main()
