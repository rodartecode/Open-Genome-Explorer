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

### Using GCS

It is possible to set up a Google Cloud Service bucket to hold the somewhat sizable files and allow scalability. To do this you must first set up a GCS account and do some provisioning.

> Note: Instructions taken from <https://github.com/learn-py4web/gcs_file_storage>

#### Configure the upload bucket on GCS

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

Finally, you must set `USE_GCS` to `True` in the `settings.py` file
