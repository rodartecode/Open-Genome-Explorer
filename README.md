# Open Genome Explorer

## About Open Genome Explorer

tbd

## Usage

tbd

## Initial Setup

### Install Dependencies

From the root directory run

```bash
pip -r requirements.txt
```

### Create secrets file

If it doesn't exist already create a folder called `private` in the `apps/OpenGenomeExplorer` directory. Refer to `apps/OpenGenomeExplorer/example_secrets.py` for the contents required. You can copy the contents of this file to `apps/OpenGenomeExplorer/private/secrets.py`.
This app uses Google oauth for authentication. If you only plan to run the app locally then you must simply provide the OAUTH client_id and secret to run the app.
Refer to <https://developers.google.com/workspace/guides/configure-oauth-consent> for instructions on generating these tokens.

If you want to deploy the app to Google App Engine refer to the README in the `deployment_tools/gae` directory for further instructions.

### Run

From the root directory run the app with

```bash
py4web run apps
```

### Using GAE

With some configuration it is possible to deploy this app on Google App Engine. This app uses a Google Cloud MySQLDB for relational db data, and Google Cloud Service bucket to hold the somewhat sizable files and allow scalability. To do this you must first set up a GCS account and do some provisioning.

Refer to `deployment_tools/gae/README.md` for further instructions.
