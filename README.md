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

### Run

From the root directory run the app with

```bash
py4web run apps
```

### Using GAE

With some configuration it is possible to deploy this app on Google App Engine. This app uses a Google Cloud MySQLDB for relational db data, and Google Cloud Service bucket to hold the somewhat sizable files and allow scalability. To do this you must first set up a GCS account and do some provisioning.

#### Configure the file upload bucket on GCS

> Note: Instructions taken from <https://github.com/learn-py4web/gcs_file_storage>

* Create a [Google Cloud Project](https://console.cloud.google.com), and
  [configure billing](https://console.cloud.google.com/billing).
* [Create a storage bucket](https://console.cloud.google.com/storage/browser).  
* Create a [service account](https://console.cloud.google.com/iam-admin/serviceaccounts), with a name such as `filemanager@yourproject.
  iam.gserviceaccount.com`, where `filemanager` is the name of the "user" for the account, and `yourproject` is the name of the service account.
* Download the json credentials for the above service account, and store them in a file in `private/gcs_keys.json` in this app.  Make sure the file is also in `.gitignore`!
* Go to the [Google Cloud Console, then to Storage, then to Browse](https://console.cloud.google.com/storage/browser).  Click
  on the bucket options on the right, then on _permissions_, and add the
  service account with the permission _Storage Object Admin_ to the bucket permissions.
* Set up the bucket for CORS.  [Install `gsutils` if needed](<https://cloud.google.com/storage/docs/gsutil_install>), then run:

```bash
gsutil cors set /path/to/cors_json_file.json gs://bucketname
```

#### Initialize Google App Engine Project and DB

coming soon but mostly adapted from <https://learn-py4web.github.io/unit20.html>

#### Manually Migrate the DB

In Google App Engine the database tables need to be manually created so that PYdal can use them.

```SQL
coming soon
```
