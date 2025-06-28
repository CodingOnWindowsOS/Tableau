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
        # Gather all flows.
        flows = [flow for flow in tsc.Pager(server.flows)]
        # Gather flow run history.
        runs = [run for run in tsc.Pager(server.flow_runs)]
        # Gather all users.
        users = [user for user in tsc.Pager(server.users)]

    # Create a dataframe containing flow information.
    flow_info = pd.DataFrame(
        [
            {
                'Flow ID': flow.id,
                'Flow Owner ID': flow.owner_id,
                'Flow Name': flow.name,
                'Flow Project ID': flow.project_id,
                'Flow Project Name': flow.project_name,
                'Flow Content URL': flow.webpage_url
            }
            for flow in flows
        ]
    )

    # Create a dataframe containing flow execution history.
    flow_run_history = pd.DataFrame(
        [
            {
                'Flow ID': run.flow_id,
                'Run Duration': run.completed_at - run.started_at
            }
            for run in runs
        ]
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

    # Create a dataframe containing user information.
    user_info = pd.DataFrame(
        [
            {
                'User ID': user.id,
                'User Display Name': user.fullname,
                'User Email Address': user.email,
                'User Site Role': user.site_role,
            }
            for user in users
        ]
    )

    # Create a flows report by merging flow info, flow run summary, and user info dataframes.
    flows_report = (
        flow_info
        .merge(
            right=user_info,
            how='left',
            left_on='Flow Owner ID',
            right_on='User ID'
        )
        .drop(columns=['User ID'])
        .merge(
            right=flow_run_summary,
            how='left',
            on='Flow ID'
        )
    )
        
    # Create and write flows report dataframe to specified file path.
    write_path = pathlib.Path(
        f'C:/Users/Chris/OneDrive/Desktop/social_media_content/youtube/tableau_server_client/tutorial_9/flows_report_'\
        f'{datetime.now(tz=timezone.utc).strftime("%Y%m%d%H%M%S")}.xlsx'
    )

    with pd.ExcelWriter(write_path) as writer:
        flows_report.to_excel(writer, sheet_name='Flows', index=False)

if __name__ == '__main__':
    main()
