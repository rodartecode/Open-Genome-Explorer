# Deploying to Google App Engine

## Set up Google App Engine Services

### Configure the file upload bucket on GCS

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

### Initialize Google App Engine Project and DB

coming soon but mostly adapted from <https://learn-py4web.github.io/unit20.html>

### Manually Migrate the DB

In Google App Engine the database tables need to be manually created so that PYdal can use them. In addition future migrations will also need to be done manually.

```SQL
coming soon
```

### To deploy code on Google App Engine

```bash
cd deployment_tools/gae
make setup
mkdir apps
touch apps/__init__.py
# symlink the apps that you want to deploy to GAE, for example:
cd apps
ln -s ../../../apps/_default .
ln -s ../../../apps/.service . 
cd ..
```

Then, you can either do:

```bash
make deploy email={your email} project={your project} version={vesion}
```

or if you have a gcloud configuration already configured,

```bash
gcloud app deploy
```
