import datetime
import random

from py4web import action, request, abort, redirect, URL
from yatl.helpers import A
from .common import db, session, T, cache, auth, logger, authenticated, unauthenticated, flash
from py4web.utils.url_signer import URLSigner
from .models import get_username
import firebase_admin
from firebase_admin import auth as fb_auth
from firebase_admin import credentials
import pickle
import json, requests, threading, queue, time, string
import asyncio


# Some constants.
MAX_RETURNED_USERS = 20 # Our searches do not return more than 20 users.
MAX_RESULTS = 20 # Maximum number of returned meows. 

url_signer = URLSigner(session)

@action('index')
@action.uses('index.html', url_signer, db, auth.user)
def index():
    auth_verify_url = URL('auth_verify', signer=url_signer)
    get_snps_url = URL('get_SNPs', signer=url_signer)
    file_upload_url = URL('file_upload', signer=url_signer)

    #print("Meow URL:", get_meows_url)
    return dict(file_upload_url=file_upload_url, get_snps_url=get_snps_url, auth_verify_url=auth_verify_url)

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

async def process_snps(file):

    # TODO: Remember to process the raw file first, this doesn't do that yet
    # TODO: Issue with full length
    for line in file.split("\n")[0:100]:
        try:
            split_line = line.split("\t")
            rsid = split_line[0]
            alleles = split_line[1]
            if (alleles != "--"):
                allele1 = alleles[0]
                allele2 = alleles[1]

                opensnp_url = "https://opensnp.org/snps/json/annotation/" + rsid + ".json"

                # Fetch information using requests module
                # and parse with json module
                response = requests.Session().get(opensnp_url)
                data = json.loads(response.text)

                traits = {}
                for each in data["snp"]["annotations"]["snpedia"]:
                    traits[each["url"][-4] + each["url"][-2]] = each["summary"][0:len(each["summary"])-1]

                

                db.SNP.insert(rsid=rsid, allele1=allele1, allele2=allele2)
        except Exception as e:
            print(e)

@action('auth_verify', method=["POST"])
@action.uses(url_signer.verify(), auth.user)
def auth_verify():
    uid = str(auth.user_id) + ":" + get_username()

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
@action.uses(url_signer.verify(), db, auth.user)
def file_upload():
    print("entered file upload")
    file_name = request.params.get("file_name")
    file_type = request.params.get("file_type")
    uploaded_file = request.body # This is a file, you can read it.
    # Diagnostics
    #print("Uploaded", file_name, "of type", file_type)
    #print("Content:", uploaded_file.read())
    file = uploaded_file.read().decode('UTF-8')
    #print("file:", file.split("\n")[0])

    asyncio.run(process_snps(file))

    return "ok"