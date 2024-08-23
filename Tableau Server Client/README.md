# Automation with Tableau Server Client (TSC)
Use these python (.py) files/scripts corresponding to each of my Tableau Server Client tutorials featured on my YouTube channel to save time and hundreds, if not thousands of clicks through automation.

1. Getting Started
   - Learn to authenticate and sign-in to your Tableau Server or Tableau Cloud instance for the first time. Updates to the token value are required unless you are also using the keyring module to store and retrieve your personal access tokens.
   - Query your server for the first time to retrieve information on all data sources published and maintained on your Tableau Server or Tableau Cloud instance.

2. Generating Reports
   - Use these scripts to automate the generation of reports on various content and object types (e.g., flows, users, workbooks, data sources, etc.).

3. Refreshing Data
   - Automate the execution of flows, linked tasks, and extract refreshes on your Tableau Server or Tableau Cloud instance using these scripts.
   - Implement conditional execution logic that is not currently supported by Tableau Server and Tableau Cloud products.
   - Refresh your data at frequencies not currently supported by Tableau Server and Tableau Cloud products.

#### Generating Personal Access Tokens
To generate a personal access token (i.e., token_value as shown in the scripts), do the following:
1. Navigate to your accounts settings (My Account Settigns) on your Tableau Server or Tableau Cloud instance.
2. Scroll down to the Personal Access Tokens Section.
3. Type/enter in your preferred token name and click "Create Token."
4. Copy/paste the generated token into the python script as the token_value.
