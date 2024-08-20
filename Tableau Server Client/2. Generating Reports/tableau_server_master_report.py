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
        # Gather all users.
        users = [user for user in tsc.Pager(server.users)]
        # Populate the favorite list for each user.
        for user in users:
            server.users.populate_favorites(user)
        # Gather all groups.
        groups = [group for group in tsc.Pager(server.groups)]
        # Populate the user info for each user within each group.
        for group in groups:
            server.groups.populate_users(group)
        # Create a dataframe containing group information, including user membership.
        group_info = pd.DataFrame(
            {
                'Group ID': [group.id for group in groups],
                'Group Name': [group.name for group in groups],
                'Group Domain': [group.domain_name for group in groups],
                'Users': [[user.id for user in group.users] for group in groups]
            }
        )
        # Gather all projects.
        projects = [project for project in tsc.Pager(server.projects)]
        # Gather all data sources.
        data_sources = [data_source for data_source in tsc.Pager(server.datasources)]
        # Gather all workbooks.
        workbooks = [workbook for workbook in tsc.Pager(server.workbooks)]
        # Gather all workbook views (i.e., sheets).
        views = [view for view in tsc.Pager(server.views, usage=True)]
        # Gather all flows.
        flows = [flow for flow in tsc.Pager(server.flows)]
        # Gather flow run history.
        runs = [run for run in tsc.Pager(server.flow_runs)]
        # Gather all subscriptions.
        subscriptions = [subscription for subscription in tsc.Pager(server.subscriptions)]
        
    # Create a dataframe containing user information.
    user_info = pd.DataFrame(
        {
            'User ID': [user.id for user in users],
            'User Display Name': [user.fullname for user in users],
            'User Email Address': [user.email for user in users],
            'User Site Role': [user.site_role for user in users]
        }
    )

    # Gather user ID values for owners of flows, data sources, and workbooks.
    flow_owners = [flow.owner_id for flow in flows]
    data_source_owners = [data_source.owner_id for data_source in data_sources]
    workbook_owners = [workbook.owner_id for workbook in workbooks]

    # Get unique ID values across each list and consolidate those values into one list.
    flow_owners = set(flow_owners)
    data_source_owners = set(data_source_owners)
    workbook_owners = set(workbook_owners)
    flow_owners.update(data_source_owners)
    flow_owners.update(workbook_owners)
    owners = set(flow_owners)

    # Create a user report based on the user info dataframe.
    users_report = (
        user_info
        .assign(
            is_owner=user_info['User ID'].isin(owners)
        )
        .rename(columns={'is_owner': 'Content Owner'})
        .sort_values(by='Content Owner', ascending=False)
    )

    # Gather all user favorites across each category type (e.g., workbook, flow, data source, etc.).
    all_favorites = []
    for user in users:
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

    # Transform dataframe to be display one row per group per user.
    group_info = group_info.explode(column='Users')

    # Create a groups report by merging project info and user info dataframes.
    groups_report = (
        group_info
        .merge(
            right=user_info,
            how='left',
            left_on='Users',
            right_on='User ID'
        )
        .drop(columns=['User ID'])
    )

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

    # Create a dataframe containing data source information.
    data_source_info = pd.DataFrame(
        {
            'Data Source ID': [data_source.id for data_source in data_sources],
            'Data Source Owner ID': [data_source.owner_id for data_source in data_sources],
            'Data Source Name': [data_source.name for data_source in data_sources],
            'Data Source Type': [data_source.datasource_type for data_source in data_sources],
            'Data Source Created At': [data_source.created_at for data_source in data_sources],
            'Data Source Updated At': [data_source.updated_at for data_source in data_sources],
            'Data Source Project ID': [data_source.project_id for data_source in data_sources],
            'Data Source Project Name': [data_source.project_name for data_source in data_sources]
        }
    )

    # Create a data sources report by merging data source info and user info dataframes.
    data_sources_report = (
        data_source_info
        .merge(
            right=user_info,
            how='inner',
            left_on='Data Source Owner ID',
            right_on='User ID',
        )
        .drop(columns=['User ID'])
        .rename(
            columns={
                'User Display Name': 'Data Source Owner Name',
                'User Email Address': 'Data Source Owner Email Address',
                'User Site Role': 'Data Source Owner Site Role'
            }
        )
        .reindex(
            columns=[
                'Data Source ID', 'Data Source Name',
                'Data Source Type', 'Data Source Created At',
                'Data Source Updated At', 'Data Source Project ID',
                'Data Source Project Name', 'Data Source Owner ID',
                'Data Source Owner Name', 'Data Source Owner Email Address',
                'Data Source Owner Site Role'
            ]
        )
    )

    # Remove the timezone information from each value in order to write to excel file.
    data_sources_report['Data Source Created At'] = data_sources_report['Data Source Created At'].dt.tz_localize(None)
    data_sources_report['Data Source Updated At'] = data_sources_report['Data Source Updated At'].dt.tz_localize(None)

    # Create a dataframe containing workbook information.
    workbook_info = pd.DataFrame(
        {
            'Workbook ID': [workbook.id for workbook in workbooks],
            'Workbook Owner ID': [workbook.owner_id for workbook in workbooks],
            'Workbook Name': [workbook.name for workbook in workbooks],
            'Workbook Created At': [workbook.created_at for workbook in workbooks],
            'Workbook Updated At': [workbook.updated_at for workbook in workbooks],
            'Workbook Content URL': [workbook.webpage_url for workbook in workbooks],
            'Workbook Project ID': [workbook.project_id for workbook in workbooks],
            'Workbook Project Name': [workbook.project_name for workbook in workbooks]
        }
    )

    # Create a dataframe containing the number of views per workbook.
    total_views_per_workbook = (
        pd.DataFrame([view.__dict__ for view in views])
        .groupby('_workbook_id')['_total_views']
        .sum()
        .reset_index()
        .rename(
            columns={
                '_workbook_id': 'Workbook ID',
                '_total_views': 'Workbook Total Views'
            }
        )
    )

    # Create a workbooks report by merging workbook info, view info, and user info dataframes.
    workbooks_report = (
        workbook_info
        .merge(
            right=total_views_per_workbook,
            how='inner',
            on='Workbook ID'
        )
        .merge(
            right=user_info,
            how='inner',
            left_on='Workbook Owner ID',
            right_on='User ID'
        )
        .drop(columns=['User ID'])
        .rename(
            columns={
                'User Display Name': 'Workbook Owner Name',
                'User Email Address': 'Workbook Owner Email Address',
                'User Site Role': 'Workbook Owner Site Role'
            }
        )
        .reindex(
            columns=[
                'Workbook ID', 'Workbook Name',
                'Workbook Total Views', 'Workbook Created At',
                'Workbook Updated At', 'Workbook Content URL',
                'Workbook Project ID', 'Workbook Project Name',
                'Workbook Owner ID', 'Workbook Owner Name',
                'Workbook Owner Email Address', 'Workbook Owner Site Role'
            ]
        )
    )

    # Remove the timezone information from each value in order to write to excel file.
    workbooks_report['Workbook Created At'] = workbooks_report['Workbook Created At'].dt.tz_localize(None)
    workbooks_report['Workbook Updated At'] = workbooks_report['Workbook Updated At'].dt.tz_localize(None)

    # Create a dataframe containing flow information.
    flow_info = pd.DataFrame(
        {
            'Flow ID': [flow.id for flow in flows],
            'Flow Owner ID': [flow.owner_id for flow in flows],
            'Flow Name': [flow.name for flow in flows],
            'Flow Project ID': [flow.project_id for flow in flows],
            'Flow Project Name': [flow.project_name for flow in flows],
            'Flow Content URL': [flow.webpage_url for flow in flows]
        }
    )

    # Create a dataframe containing flow execution history.
    flow_run_history = pd.DataFrame(
        {
            'Flow ID': [run.flow_id for run in runs],
            'Run Duration': [run.completed_at - run.started_at for run in runs]
        }
    )

    # Create a data frame containing the execution summary.
    flow_run_summary = (
        flow_run_history
        .groupby('Flow ID')['Run Duration']
        .agg(['count', 'sum', 'mean', 'max', 'min'])
        .assign(duration_range=lambda flow: flow['max'] - flow['min'])
        .reset_index()
        .rename(
            columns={
                'count': 'Run Count',
                'sum': 'Total Duration',
                'mean': 'Average Duration',
                'max': 'Maximum Duration',
                'min': 'Minimum Duration',
                'duration_range': 'Duration Range'
            }
        )
    )

    # Convert each duration-based measure from timedelta data type to raw seconds.
    flow_run_summary['Total Duration'] = flow_run_summary['Total Duration'].dt.total_seconds()
    flow_run_summary['Average Duration'] = flow_run_summary['Average Duration'].dt.total_seconds()
    flow_run_summary['Maximum Duration'] = flow_run_summary['Maximum Duration'].dt.total_seconds()
    flow_run_summary['Minimum Duration'] = flow_run_summary['Minimum Duration'].dt.total_seconds()
    flow_run_summary['Duration Range'] = flow_run_summary['Duration Range'].dt.total_seconds()

    # Create a flows report by merging flow info, flow run summary, and user info dataframes.
    flows_report = (
        flow_info
        .merge(
            right=user_info,
            how='inner',
            left_on='Flow Owner ID',
            right_on='User ID'
        )
        .drop(columns=['User ID'])
        .merge(
            right=flow_run_summary,
            how='inner',
            on='Flow ID'
        )
    )

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
        [
            workbook_info
            .loc[:, ['Workbook ID', 'Workbook Owner ID', 'Workbook Name', 'Workbook Content URL']]
            .rename(
                columns={
                    'Workbook ID': 'Content ID',
                    'Workbook Owner ID': 'Content Owner ID',
                    'Workbook Name': 'Content Name',
                    'Workbook Content URL': 'Content URL'
                }
            ),
            view_info
        ],
        axis=0,
        ignore_index=True
    )

    # Create a subscriptions report by merging the subscription info, workbook info, view info, and user info dataframes.
    subscriptions_report = pd.DataFrame(
        subscription_info
        .merge(
            right=content_info,
            how='inner',
            left_on='Subscription Content ID',
            right_on='Content ID'
        )
        .drop(columns=['Subscription Content ID'])
        .merge(
            right=user_info,
            how='inner',
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
            how='inner',
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

    # Create and write object-specific dataframes to specified file path.
    write_path = pathlib.Path(
        f'C:/Users/Chris/Desktop/social_media_content/youtube/tableau_server_client/tutorial_12/master_report_'\
        f'{datetime.now(tz=timezone.utc).strftime("%Y%m%d%H%M%S")}.xlsx'
    )

    # Write each report to an individual sheet within a single excel workbook.
    with pd.ExcelWriter(write_path) as writer:
        users_report.to_excel(writer, sheet_name='Users', index=False)
        favorites_report.to_excel(writer, sheet_name='Favorites', index=False)
        groups_report.to_excel(writer, sheet_name='Groups', index=False)
        projects_report.to_excel(writer, sheet_name='Projects', index=False)
        data_sources_report.to_excel(writer, sheet_name='Data Sources', index=False)
        workbooks_report.to_excel(writer, sheet_name='Workbooks', index=False)
        flows_report.to_excel(writer, sheet_name='Flows', index=False)
        subscriptions_report.to_excel(writer, sheet_name='Subscriptions', index=False)

if __name__ == '__main__':
    main() 