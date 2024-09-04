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
                tsc.RequestOptions.Operator.Equals,
                'North America Sales (extract refresh demo)'
            )
        )
        # Get the extract specified in the request filter.
        data_source = server.datasources.get(request_options)[0][0]
        # Trigger the extract refresh and wait for the response.
        job = server.datasources.refresh(data_source)
        print(f'Job {job.id} is running.')
        try:
            job = server.jobs.wait_for_job(job)
        except:
            response = 'Job failed.'
            print(response)
        else:
            response = (
                'Job finished succesfully\n\n'
                'Job Details\n'
                f'Job ID: {job.id}\n'
                f'Flow Name: {data_source.name}\n'
                f'Job Created Time: {job.started_at}\n'
                f'Job Start Time: {job.started_at}\n'
                f'Job End Time: {job.completed_at}\n'
            )
            print(response)

if __name__== '__main__':
    main()