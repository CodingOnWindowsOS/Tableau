# Day Zero Project Hierarchy
Today is the day. Your team is standing up their Tableau Server in preparation for next week’s global roll-out. One of the tasks you have been assigned is to create a series of projects (i.e., folders) on the server that aligns with the organizational structure.

The organization’s structure consists of the following five regions, North America, Brazil, UK&I, Spanish Latam, EMEA, and APAC. Each of those regions is comprised of nine divisions, Marketing, Sales, Technology, Operations, Finance, Customer Support, Product, Legal, and Human Resources.

Use the Tableau Server Client (TSC) python library to create the organizational structure, programattically. Start off by manually creating a "DataDevQuest Challenge" project using Tableau's front-end user interface. This is the project where the new organizational structure will be maintained within. Upon completing the challenge, the DataDevQuest Challenge project hierarchy should look the one below.

<details>
  <summary>Click to view the expected hierarchy.</summary>
  
    - DataDevQuest Challenge  
      - APAC  
        - Marketing  
        - Sales  
        - Technology  
        - Operations  
        - Finance  
        - Customer Support  
        - Product  
        - Legal  
        - Human Resources  
      - Brazil  
        - Marketing  
        - Sales  
        - Technology  
        - Operations  
        - Finance  
        - Customer Support  
        - Product  
        - Legal  
        - Human Resources  
      - EMEA  
        - Marketing  
        - Sales  
        - Technology  
        - Operations  
        - Finance  
        - Customer Support  
        - Product  
        - Legal  
        - Human Resources  
      - North America  
        - Marketing  
        - Sales  
        - Technology  
        - Operations  
        - Finance  
        - Customer Support  
        - Product  
        - Legal  
        - Human Resources  
      - Spanish Latam  
        - Marketing  
        - Sales  
        - Technology  
        - Operations  
        - Finance  
        - Customer Support  
        - Product  
        - Legal  
        - Human Resources  
      - UK&I  
        - Marketing  
        - Sales  
        - Technology  
        - Operations  
        - Finance  
        - Customer Support  
        - Product  
        - Legal
</details>

# Tutorial
<details>
  <summary>Click to begin reading the tutorial.</summary>

Create an environment (.env) file and place it in the same directory as the python file dedicated to this tutorial for ease-of-access. The contents of the .env file used for this tutorial can be found below.

TABLEAU_SERVER_FULL_URL=https://10ax.online.tableau.com/#/site/sqlshortreads
TABLEAU_SERVER_SITE_ID=sqlshortreads
TABLEAU_SERVER_TOKEN_NAME=TSM
TABLEAU_SERVER_TOKEN_VALUE=VmhlQ6HbQDqr9QF/AZiQ9g==:n3RsYPPNt8w6covEZG9f37Kn4KTf8M0G
TABLEAU_VERIFY_CERTIFICATE=False

Import the necessary packages. Each of these packages will be discussed in turn.

Use package, os and dotenv, to load your environment file and allow its variables to be accessed. This step is critical for accessing your Tableau Server or Tableau Cloud instance, programmatically.

```python
# Load environment variables from .env file.
load_dotenv()
TABLEAU_SERVER_FULL_URL = os.getenv('TABLEAU_SERVER_FULL_URL')
TABLEAU_SERVER_SITE_ID = os.getenv('TABLEAU_SERVER_SITE_ID')
TABLEAU_SERVER_TOKEN_NAME = os.getenv('TABLEAU_SERVER_TOKEN_NAME')
TABLEAU_SERVER_TOKEN_VALUE = os.getenv('TABLEAU_SERVER_TOKEN_VALUE')
TABLEAU_VERIFY_CERTIFICATE = os.getenv('TABLEAU_VERIFY_CERTIFICATE', 'True') == 'True'
```
Create a means to authenticate with your Tableau Server or Tableau Cloud instance by using TSC’s PersonalAccessTokenAuth class. Pass in the environment variables that correspond to token name, token value, and site ID, if applicable. If you are using Tableau Server and use the default site, then your site ID value should be None or an empty string.

```python
# Create authentication object using the token and site ID details.
TABLEAU_AUTHENTICATION = tsc.PersonalAccessTokenAuth(
  token_name=TABLEAU_SERVER_TOKEN_NAME,
  personal_access_token=TABLEAU_SERVER_TOKEN_VALUE,
  site_id=TABLEAU_SERVER_SITE_ID
)
```

Next, create an instance of TSC’s Server class and pass in the base URL associated with your Tableau Server or Tableau Cloud instance. If you are authenticating with a Tableau Server that uses the default site, then the full server URL and the base URL will be identical. Otherwise, be sure to exclude the site ID from the URL. Optionally, choose not to verify the server's SSL/TLS certificate. If you are authenticating with a Tableau Cloud instance, maintaining the default value of True is unlikely to cause you any problems. I have only seen and experienced an issue with the default value when using Tableau Server instances maintained by the companies I have worked for.

```python
# Create a tableau server client object using specified server URL.
SERVER = tsc.Server('https://10ax.online.tableau.com')
# Disable certificate verification. The next line of code may be required due to certificate issues.
SERVER.add_http_options({'verify': False})
```

Now, read in the organizational structure maintained within the CSV file provided and create a python dictionary containing a key for each unique region. Each key’s value should be the respective region’s divisions as a python list. Keep in mind, there are several ways to achieve the desired dictionary structure and the strategy shown below is just one way.

```python
# Read in organizational structure from a CSV file.
ORGANIZATIONAL_STRUCTURE = pd.read_csv('organizational_structure.csv')
# Create a mapping of regions to their respective divisions.
region_division_mapping = (
  ORGANIZATIONAL_STRUCTURE
  .groupby('Region')['Division']
  .unique()
  .apply(list)
  .to_dict()
)
```

Aside from reading in the organizational structure and subsequently creating the region-division mapping, the previous steps are those that you will find yourself repeating throughout your future scripts aimed at interacting with your Tableau Server or Tableau cloud instance, programmatically, through Tableau Server Client.
</details>

# Solution
<details>
  <summary>Click to view the solution.</summary>
  
  ```python
import os

from dotenv import load_dotenv
import pandas as pd
import tableauserverclient as tsc
from time import sleep

# Load environment variables from .env file.
load_dotenv()
TABLEAU_SERVER_FULL_URL = os.getenv('TABLEAU_SERVER_FULL_URL')
TABLEAU_SERVER_SITE_ID = os.getenv('TABLEAU_SERVER_SITE_ID')
TABLEAU_SERVER_TOKEN_NAME = os.getenv('TABLEAU_SERVER_TOKEN_NAME')
TABLEAU_SERVER_TOKEN_VALUE = os.getenv('TABLEAU_SERVER_TOKEN_VALUE')
TABLEAU_VERIFY_CERTIFICATE = os.getenv('TABLEAU_VERIFY_CERTIFICATE', 'True') == 'True'

# Create authentication object using the token and site ID details.
TABLEAU_AUTHENTICATION = tsc.PersonalAccessTokenAuth(
    token_name=TABLEAU_SERVER_TOKEN_NAME,
    personal_access_token=TABLEAU_SERVER_TOKEN_VALUE,
    site_id=TABLEAU_SERVER_SITE_ID
)
# Create a tableau server client object using specified server URL.
SERVER = tsc.Server('https://10ax.online.tableau.com')
# Disable certificate verification. The next line of code may be required due to certificate issues.
SERVER.add_http_options({'verify': False})
# Read in organizational structure from a CSV file.
ORGANIZATIONAL_STRUCTURE = pd.read_csv('organizational_structure.csv')
# Create a mapping of regions to their respective divisions.
region_division_mapping = (
    ORGANIZATIONAL_STRUCTURE
    .groupby('Region')['Division']
    .unique()
    .apply(list)
    .to_dict()
)
# Sign-in to server.
with SERVER.auth.sign_in(TABLEAU_AUTHENTICATION):
    # Ensure the most recent Tableau REST API version is used.
    SERVER.use_highest_version()
    # Extract the parent project ID for the 'DataDevQuest Challenge' project where the new projects will be created.
    parent_project_id = SERVER.projects.filter(name='DataDevQuest Challenge')[0].id
    # For each region, create a new project and then create the division projects within it.
    for region, divisions in region_division_mapping.items():
        new_region_project = tsc.ProjectItem(
            name=region,
            description=f'Parent project for {region} divisions.',
            parent_id=parent_project_id
        )
        SERVER.projects.create(project_item=new_region_project)
        # Wait for a short period to ensure the project is created before proceeding.
        sleep(2)
        # Extract the ID of the newly created region project to use as a parent for division projects.
        region_project_id = SERVER.projects.filter(name=region)[0].id
        new_division_projects = [
            tsc.ProjectItem(
                name=division,
                description=f"Project for {region}'s {division} division.",
                parent_id=region_project_id
            )
            for division in divisions
        ]
        # Create each division project under the newly created region project.
        for new_division_project in new_division_projects:
            SERVER.projects.create(project_item=new_division_project)
```
