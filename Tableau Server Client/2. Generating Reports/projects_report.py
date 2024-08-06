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
        # Gather all projects.
        projects = [project for project in tsc.Pager(server.projects)]
        # Gather all users.
        users = [user for user in tsc.Pager(server.users)]

    # Create a dataframe containing project information.
    project_info = pd.DataFrame(
        {
            'Project ID': [project.id for project in projects],
            'Project Name': [project.name for project in projects],
            'Project Description': [project.description for project in projects],
            'Project Owner ID': [project.owner_id for project in projects],
            'Parent Project ID': [project.parent_id for project in projects]
        }
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
    
    # Create a projects report by merging project info and user info dataframes.
    projects_report =(
        project_info
        .merge(
            right=project_info,
            how='left',
            left_on='Parent Project ID',
            right_on='Project ID',
            suffixes=(
                '',
                ' Parent'
            ),
        )
        .drop(
            columns=[
                'Parent Project ID Parent',
                'Project ID Parent'
            ]
        )
        .rename(
            columns={
                'Project Name Parent': 'Parent Project Name',
                'Project Description Parent': 'Parent Project Description',
                'Project Owner ID Parent': 'Parent Project Owner ID'
            }
        )
        .merge(
            right=user_info,
            how='left',
            left_on='Project Owner ID',
            right_on='User ID'
        )
        .drop(columns=['User ID'])
        .rename(
            columns={
                'User Display Name': 'Project Owner Name',
                'User Email Address': 'Project Owner Email Address',
                'User Site Role': 'Project Owner Site Role'
            }
        )
        .merge(
            right=user_info,
            how='left',
            left_on='Parent Project Owner ID',
            right_on='User ID'
        )
        .drop(columns=['User ID'])
        .rename(
            columns={
                'User Display Name': 'Parent Project Owner Name',
                'User Email Address': 'Parent Project Owner Email Address',
                'User Site Role': 'Parent Project Owner Site Role'
            }
        )
        .reindex(
            columns=[
                'Project ID', 'Project Name', 'Project Description',
                'Project Owner ID', 'Project Owner Name', 'Project Owner Email Address',
                'Project Owner Site Role', 'Parent Project ID', 'Parent Project Name',
                'Parent Project Description', 'Parent Project Owner ID', 'Parent Project Owner Name',
                'Parent Project Owner Email Address', 'Parent Project Owner Site Role'
            ]
        )
    )
        
    # Create and write projects report dataframe to specified file path.
    write_path = pathlib.Path(
        f'C:/Users/Chris/Desktop/social_media_content/youtube/tableau_server_client/tutorial_6/projects_report_'\
        f'{datetime.now(tz=timezone.utc).strftime("%Y%m%d%H%M%S")}.xlsx'
    )

    with pd.ExcelWriter(write_path) as writer:
        projects_report.to_excel(writer, sheet_name='Projects', index=False)

if __name__ == '__main__':
    main()
