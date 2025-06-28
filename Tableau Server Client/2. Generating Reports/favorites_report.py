from datetime import datetime, timezone
import pathlib

import keyring
import pandas as pd
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
        # Gather all users.
        users = [user for user in tsc.Pager(server.users)]
        # Gather all user favorites across each category type (e.g., workbook, flow, data source, etc.).
        all_favorites = []
        for user in users:
            server.users.populate_favorites(user)
            favorite_categories = [category for category in user.favorites.keys() if user.favorites[category]]
            for category in favorite_categories:
                category_favorites = pd.DataFrame(data=user.favorites[category], columns=['Favorite'])
                category_favorites = (
                    category_favorites
                    .assign(
                        favorite_id=category_favorites['Favorite'].apply(lambda favorite: favorite.id),
                        favorite_name=category_favorites['Favorite'].apply(lambda favorite: favorite.name),
                        favorite_category=category.title(),
                        favorite_project_id=category_favorites['Favorite'].apply(
                            lambda favorite: getattr(favorite, 'project_id', 'Not applicable')
                        ),
                        favorite_project_name=category_favorites['Favorite'].apply(
                            lambda favorite: getattr(favorite, 'project_name', 'Not applicable')
                        ),
                        user_id=user.id,
                        user_display_name=user.fullname,
                        user_email_address=user.email,
                        user_site_role=user.site_role
                    )
                )
                all_favorites.append(category_favorites)

    # Create a dataframe containing favorite information.
    favorites_report = (
        pd.concat(
            all_favorites,
            axis=0,
            ignore_index=True
        )
        .drop(columns=['Favorite'])
        .rename(
            lambda column: column.replace('_', ' ').title().replace('Id', 'ID'),
            axis=1
        )
    )
     
    # Create and write favorites report dataframe to specified file path.
    write_path = pathlib.Path(
        f'C:/Users/Chris/Desktop/social_media_content/youtube/tableau_server_client/tutorial_11/favorties_report_'\
        f'{datetime.now(tz=timezone.utc).strftime("%Y%m%d%H%M%S")}.xlsx'
    )

    with pd.ExcelWriter(write_path) as writer:
        favorites_report.to_excel(writer, sheet_name='Favorites', index=False)

if __name__ == '__main__':
    main() 
