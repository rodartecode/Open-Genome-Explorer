import datetime
import random
import os
import uuid
import re

from py4web import action, request, abort, redirect, URL
from yatl.helpers import A
from .common import db, session, T, cache, auth, logger, authenticated, unauthenticated, flash
from py4web.utils.url_signer import URLSigner
from .models import get_username, get_user_email
import firebase_admin
from firebase_admin import auth as fb_auth
from firebase_admin import credentials
import pickle
import json, requests, threading, queue, time, string
import asyncio
from nqgcs import NQGCS
from .gcs_url import gcs_url
from .settings import APP_FOLDER

url_signer = URLSigner(session)
BUCKET = "/open-genome-explorer"
GCS_KEY_PATH =  os.path.join(APP_FOLDER, 'private/gcs_keys.json')
with open(GCS_KEY_PATH) as f:
    GCS_KEYS = json.load(f) # Load keys
nqgcs = NQGCS(keys=GCS_KEYS) # Luca's handle to GCS

@action('index')
@action.uses('index.html', url_signer, db, auth.user)
def index():
    auth_verify_url = URL('auth_verify', signer=url_signer)
    get_snps_url = URL('get_SNPs', signer=url_signer)
    file_upload_url = URL('file_upload', signer=url_signer)
    # GCS links
    file_info_url = URL('file_info', signer=url_signer)
    obtain_gcs_url = URL('obtain_gcs', signer=url_signer)
    notify_url = URL('notify_upload', signer=url_signer)
    delete_url = URL('notify_delete', signer=url_signer)
    return dict(file_upload_url=file_upload_url,
                get_snps_url=get_snps_url,
                auth_verify_url=auth_verify_url,
                file_info_url=file_info_url,
                obtain_gcs_url=obtain_gcs_url,
                notify_url=notify_url,
                delete_url=delete_url)

# Code provided by Valeska
def complement(alleles):
    compDict = {'A' : 'T',
                'G' : 'C',
                'T' : 'A',
                'C' : 'G' }
    alleles = alleles.upper()

    if(len(alleles) == 2 and "D" not in alleles and "I" not in alleles):
        return compDict[alleles[0]] + compDict[alleles[1]], compDict[alleles[1]] + compDict[alleles[0]], alleles, alleles[-1::-1]
    elif("D" in alleles or "I" in alleles and len(alleles) == 2):
        return alleles, alleles[-1::-1]
    elif("D" in alleles or "I" in alleles and len(alleles) == 1):
        return alleles
    else:
        return compDict[alleles[0]], alleles

@action('auth_verify', method=["POST"])
@action.uses(url_signer.verify(), auth.user)
def auth_verify():
    username = get_username() or ""
    uid = str(auth.user_id) + ":" + username

    import os
    print("CWD:", os.getcwd())

    cred = credentials.Certificate('./service-account.json')
    default_app = firebase_admin.initialize_app(cred)

    custom_token = fb_auth.create_custom_token(uid)

    firebase_admin.delete_app(default_app)

    print("custom_token:", custom_token)

    return dict(custom_token=custom_token)

@action('get_SNPs')
@action.uses(url_signer.verify(), db, auth.user)
def get_SNPs():
    user_snps = db(db.SNP.user_id == auth.user_id).select().as_list()
    return dict(user_snps=user_snps)

@action('file_upload', method="PUT")
@action.uses(db, auth.user)
def file_upload():
    print("entered file upload")
    file_name = request.params.get("file_name")
    file_type = request.params.get("file_type")
    uploaded_file = request.body # This is a file, you can read it.
    # Diagnostics
    #print("Uploaded", file_name, "of type", file_type)
    #print("Content:", uploaded_file.read())

    asyncio.run(process_snps(uploaded_file))
    print("finished file upload")
    return "ok"


async def process_snps(file):
    SEARCH_REGEX = r"(rs\d+)\s+(\d+)\s+(\d+)\s+([ATGC])\s*([ATGC])"
    i = 0
    for line in file:
        i += 1
        if i%10000 == 0:
            print(f"now processing line number {i}")
        line = line.decode('utf8')
        result = re.search(SEARCH_REGEX, line)
        if result:
            rsid = result.group(1)
            #chromosome = result.group(2)
            #position = result.group(3)
            allele1 = result.group(4)
            allele2 = result.group(5)
            #print(f"rsid:{rsid}|chromosome:{chromosome}|position:{position}|allele1{allele1}|allele2{allele2}")

            # NOTE: this db insert is very costly; without this line a 600k line file takes 10 seconds to process
            db.SNP.update_or_insert(rsid=rsid, allele1=allele1, allele2=allele2)


# GCS Handlers
@action('file_info')
@action.uses(url_signer.verify(), db, auth.user)
def file_info():
    row = db(db.SNP_File.owner == get_user_email()).select().first()

    if row is not None and not row.confirmed:
        delete_path(row.file_path)
        row.delete_record()
        row = {}
    if row is None:
        row = {}

    file_path = row.get("file_path")
    return dict(
        file_path = file_path,
        file_type = row.get("file_type"),
        file_date = row.get("file_date"),
        file_size = row.get("file_size"),
        file_name = row.get("file_name"),
        upload_enabled = True,
        download_enabled = True,
        download_url = gcs_url(GCS_KEYS, file_path) if file_path else None
    )

@action('obtain_gcs', method="POST")
@action.uses(url_signer.verify(), db, auth.user)
def obtain_gcs():
    action = request.json.get("action")
    if action == "PUT":
        mimetype = request.json.get("mimetype")
        file_name = request.json.get("file_name")
        extension = os.path.splitext(file_name)[1]
        file_path = os.path.join(BUCKET, str(uuid.uuid1()) + extension)
        mark_possible_upload(file_path)
        signed_url = gcs_url(GCS_KEYS, file_path, verb="PUT", content_type=mimetype)
        return dict(
            signed_url = signed_url,
            file_path = file_path
        )
    elif action == "DELETE":
        file_path = request.json.get("file_path")
        if file_path:
            row = db(db.SNP_File.file_path == file_path).select().first()
            if row and row.owner == get_user_email():
                signed_url = gcs_url(GCS_KEYS, file_path, verb="DELETE")
                return dict(signed_url=signed_url, file_path=file_path)
        return dict(signed_url=None, file_path=None)
    return dict(signed_url=None, file_path=None)


@action("notify_upload", method="POST")
@action.uses(url_signer.verify(), db, auth.user)
def notify_upload():
    file_type = request.json.get("file_type")
    file_path = request.json.get("file_path")
    file_name = request.json.get("file_name")
    file_size = request.json.get("file_size")
    rows = db(db.SNP_File.owner == get_user_email()).select()
    for row in rows:
        if row.file_path != file_path:
            delete_path(row.file_path)
            row.delete_record()
    now = datetime.datetime.now()
    db.SNP_File.update_or_insert(
        ((db.upload.owner == get_user_email()) & (db.upload.file_path == file_path)),
        owner = get_user_email(),
        file_path = file_path,
        file_type = file_type,
        file_name = file_name,
        file_size = file_size,
        file_date = now,
        confirmed = True
    )
    return dict(download_url = gcs_url(GCS_KEYS, file_path, verb="GET"), file_date=now)

@action("notify_delete", method="POST")
@action.uses(url_signer.verify(), db, auth.user)
def notify_delete():
    file_path = request.json.get("file_path")
    db((db.SNP_File.file_path == file_path) & (db.SNP_File.owner == get_user_email())).delete()
    return "ok"

def delete_path(file_path):
    if file_path:
        try:
            bucket, id = os.path.split(file_path)
            nqgcs.delete(bucket[1:], id)
        except Exception as e:
            print("Error deleting", file_path, ":", e)

def delete_previous_uploads():
    previous = db(db.SNP_File.owner == get_user_email()).select()
    for row in previous:
        delete_path(row.file_path)

def mark_possible_upload(file_path):
    delete_previous_uploads()
    db.SNP_File.insert(
        owner = get_user_email(),
        file_path = file_path,
        confirmed = False
    )