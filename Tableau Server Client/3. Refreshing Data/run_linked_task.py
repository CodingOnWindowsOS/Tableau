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
        # Create a filter for the request.
        request_options = tsc.RequestOptions()
        request_options.filter.add(
            tsc.Filter(
                tsc.RequestOptions.Field.Name,
                tsc.RequestOptions.Operator.In,
                ['North America Software Sales', 'North America Hardware Sales']
            )
        )
        # Get the flows specified in the request filter.
        flows = [flow for flow in tsc.Pager(server.flows, request_options)]
        # Ensure  is always executed first.
        linked_task = sorted(flows, key=lambda flow: 0 if flow.name == 'North America Software Sales' else 1)
        # Trigger each flow to run and wait for the response.
        for flow in linked_task:
            retry = True
            # Attempt to execute the flow until it succeeds.
            while retry:
                job = server.flows.refresh(flow)
                print(f'Job {job.id} is running.')
                try:
                    job = server.jobs.wait_for_job(job)
                except:
                    response = f'Job {job.id} failed. Retrying.'
                    print(response)
                else:
                    response = (
                        'Job finished succesfully\n\n'
                        'Job Details\n'
                        f'Job ID: {job.id}\n'
                        f'Flow Name: {flow.name}\n'
                        f'Job Created Time: {job.created_at}\n'
                        f'Job Start Time: {job.started_at}\n'
                        f'Job End Time: {job.completed_at}\n'
                    )
                    print(response)
                    retry = False

if __name__ == '__main__':
    main()