# Automation with Tableau Server Client (TSC)
Use these python (.py) files/scripts corresponding to each of my Tableau Server Client tutorials featured on my YouTube channel (https://www.youtube.com/@ChrisMPerry) to save time and hundreds, if not thousands of clicks through automation.

1. Getting Started
   - Learn to authenticate and sign-in to your Tableau Server or Tableau Cloud instance for the first time. Updates to the token value are required unless you are also using the keyring module to store and retrieve your personal access tokens.
   - Query your server for the first time to retrieve information on all data sources published and maintained on your Tableau Server or Tableau Cloud instance.

2. Generating Reports
   - Use these scripts to automate the generation of reports on various content and object types (e.g., flows, users, workbooks, data sources, etc.).

3. Refreshing Data
   - Automate the execution of flows, linked tasks, and extract refreshes on your Tableau Server or Tableau Cloud instance using these scripts.
   - Implement conditional execution logic that is not currently supported by Tableau Server and Tableau Cloud products.
   - Refresh your data at frequencies not currently supported by Tableau Server and Tableau Cloud products.

4. Adding, Updating, and Removing Objects
   - Use these scripts to add/create, update, and remove/delete objects on your Tableau Server or Tableau Cloud instance.
   - Users, groups, projects, data sources, workbooks, flows, subscriptions, and favorites among other objects can be modifed programmatically.
     
#### Generating Personal Access Tokens
To generate a personal access token (i.e., token_value as shown in the scripts), do the following:
1. Navigate to your account settings (My Account Settings) on your Tableau Server or Tableau Cloud instance.
2. Scroll down to the Personal Access Tokens Section.
3. Type/enter in your preferred token name and click "Create Token."
4. Copy/paste the generated token into the python script as the token_value.

# Special Thanks
I want to give special thanks to the maintainers and individual contributors to the Tableau Server Client Python library. Without them, I wouldn’t have been able to increase my organization’s productivity to the great extent I have, nor would I be able to provide you these pre-built scripts to help you do the same!

Check out the official repository: https://github.com/tableau/server-client-python/tree/master

