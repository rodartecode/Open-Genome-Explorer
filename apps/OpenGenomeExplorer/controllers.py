import datetime
import random
import os
import uuid
import re
import json

from py4web import action, request, abort, redirect, URL
from yatl.helpers import A
from .common import db, session, T, cache, auth, logger, authenticated, unauthenticated, flash
from py4web.utils.url_signer import URLSigner
from .models import get_username, get_user_email, get_user_id, clear_db
import pickle
import json, requests, threading, queue, time, string
import asyncio
from nqgcs import NQGCS
from .gcs_url import gcs_url
from .settings import APP_FOLDER, USE_GCS

url_signer = URLSigner(session)
opensnp_data = {}
if USE_GCS:
    BUCKET = "/open-genome-explorer"
    GCS_KEY_PATH =  os.path.join(APP_FOLDER, 'private/gcs_keys.json')
    with open(GCS_KEY_PATH) as f:
        GCS_KEYS = json.load(f) # Load keys
    nqgcs = NQGCS(keys=GCS_KEYS) # Luca's handle to GCS

with open('good_snp_data.json', 'r') as f:
  opensnp_data = json.load(f)

@action('index')
@action.uses('index.html', auth)
def index():
    if auth.current_user:
        redirect(URL('home'))
    return dict()

@action('instructions')
@action.uses('instructions.html', auth)
def instructions():
    if auth.current_user:
        redirect(URL('home'))
    return dict()

@action('shared_snp')
@action.uses('shared_snp.html', url_signer, db, auth.user)
def shared_snp():
    get_shared_snps_url = URL('get_shared_SNPs', signer=url_signer)
    get_shared_sorted_snps_url = URL('get_shared_sorted_SNPs', signer=url_signer)
    return dict(get_shared_snps_url=get_shared_snps_url,
                get_shared_sorted_snps_url=get_shared_sorted_snps_url)

@action('home')
@action.uses('home.html', url_signer, db, auth.user)
def home():
    share_snp_url = URL('share_snp', signer=url_signer)
    search_snps_url = URL('search_SNPs', signer=url_signer)
    get_snps_url = URL('get_SNPs', signer=url_signer)
    file_upload_url = URL('file_upload', signer=url_signer)
    # GCS links
    file_info_url = URL('file_info', signer=url_signer)
    obtain_gcs_url = URL('obtain_gcs', signer=url_signer)
    notify_url = URL('notify_upload', signer=url_signer)
    delete_url = URL('notify_delete', signer=url_signer)
    get_sorted_snps_url = URL('get_sorted_SNPs', signer=url_signer)
    return dict(share_snp_url=share_snp_url,
                search_snps_url=search_snps_url,
                file_upload_url=file_upload_url,
                get_snps_url=get_snps_url,
                file_info_url=file_info_url,
                obtain_gcs_url=obtain_gcs_url,
                notify_url=notify_url,
                delete_url=delete_url,
                get_sorted_snps_url=get_sorted_snps_url,
                use_gcs=USE_GCS)

# Code provided by Valeska
def complement(alleles):
    compDict = {'A' : 'T',
                'G' : 'C',
                'T' : 'A',
                'C' : 'G' }
    alleles = alleles.upper()
    try:
        if(len(alleles) == 2 and "D" not in alleles and "I" not in alleles):
            return compDict[alleles[0]] + compDict[alleles[1]], compDict[alleles[1]] + compDict[alleles[0]], alleles, alleles[-1::-1]
        elif("D" in alleles or "I" in alleles and len(alleles) == 2):
            return alleles, alleles[-1::-1]
        elif("D" in alleles or "I" in alleles and len(alleles) == 1):
            return alleles
        else:
            return compDict[alleles[0]], alleles
    except Exception as e:
        print("In complement(), alleles:", alleles)
        print("Exception in complement():", e)

@action('search_SNPs')
@action.uses(url_signer.verify(), db, auth.user)
def search_SNPs():
    search_summary = str(request.params.get("search_summary")).lower().strip().replace("\n", "")
    search_rsid = str(request.params.get("search_rsid")).lower().strip().replace("\n", "")
    
    user_snps = []

    print("search summary:", search_summary, " search RSID:", search_rsid)

    if search_summary != "" and search_rsid != "":
        print("in first")
        user_snps = db((db.SNP.user_id == auth.user_id) & (db.SNP.summary.contains(search_summary) & (db.SNP.rsid.contains(search_rsid)))).select(orderby=~db.SNP.weight_of_evidence).as_list()
    elif search_summary != "":
        print("in second")
        user_snps = db((db.SNP.user_id == auth.user_id) & (db.SNP.summary.contains(search_summary))).select(orderby=~db.SNP.weight_of_evidence).as_list()
    elif search_rsid != "":
        print("in third")
        user_snps = db((db.SNP.user_id == auth.user_id) & (db.SNP.rsid.contains(search_rsid))).select(orderby=~db.SNP.weight_of_evidence).as_list()
    else:
        print("in else")
        user_snps = db((db.SNP.user_id == auth.user_id)).select(orderby=~db.SNP.weight_of_evidence).as_list()

    return dict(user_snps=user_snps)

@action('share_snp', method="POST")
@action.uses(url_signer.verify(), db, auth.user)
def share_snp():
    
    snp = request.json.get("snp")

    print("snp:", snp)
    print("snp rsid:", snp['rsid'])

    db.shared_SNP.update_or_insert(
        (db.shared_SNP.user_id == get_user_id()) & (db.shared_SNP.rsid == snp['rsid']) & (db.shared_SNP.allele1 == snp['allele1']) & (db.shared_SNP.allele2 == snp['allele2']),
        summary=snp['summary'],
        url=snp['url'], 
        rsid=snp['rsid'], 
        allele1=snp['allele1'], 
        allele2=snp['allele2'], 
        weight_of_evidence=snp['weight_of_evidence']
    )

    return dict()

@action('get_SNP_row')
@action.uses(url_signer.verify(), db, auth.user)
def get_SNP_row():
    rsid = str(request.params.get("rsid")).lower().strip().replace("\n", "")

    user_snp = db((db.SNP.user_id == auth.user_id) & (db.SNP.rsid == rsid)).select().as_list()[0]

    allele1 = user_snp['allele1']
    allele2 = user_snp['allele2']

    alleleFreq = opensnp_data[rsid]['genotype_frequency'][allele1+allele2] / sum(opensnp_data[rsid]['genotype_frequency'].values())

    return dict(user_snps=user_snp)

@action('get_shared_SNPs')
@action.uses(url_signer.verify(), db, auth.user)
def get_shared_SNPs():
    user_snps = db(db.shared_SNP).select(orderby=~db.shared_SNP.weight_of_evidence).as_list()
    return dict(user_snps=user_snps)

@action('get_SNPs')
@action.uses(url_signer.verify(), db, auth.user)
def get_SNPs():
    user_snps = db(db.SNP.user_id == auth.user_id).select(orderby=~db.SNP.weight_of_evidence).as_list()
    return dict(user_snps=user_snps)

@action('get_shared_sorted_SNPs')
@action.uses(url_signer.verify(), db, auth.user)
def get_shared_sorted_SNPs():
    # Sort by this attribute
    attr = str(request.params.get("attr"))

    # Sort by ascending or descending
    sort = str(request.params.get("sort"))

    if sort == "asc":
        user_snps = db(db.shared_SNP.user_id == auth.user_id).select(orderby=db.shared_SNP[attr]).as_list()
    else:
        user_snps = db(db.shared_SNP.user_id == auth.user_id).select(orderby=~db.shared_SNP[attr]).as_list()

    # Return sorted list
    return dict(user_snps=user_snps)

# Get user's SNPs in an order determined by the request
@action('get_sorted_SNPs')
@action.uses(url_signer.verify(), db, auth.user)
def get_sorted_SNPs():
    # Sort by this attribute
    attr = str(request.params.get("attr"))

    # Sort by ascending or descending
    sort = str(request.params.get("sort"))

    if sort == "asc":
        user_snps = db(db.SNP.user_id == auth.user_id).select(orderby=db.SNP[attr]).as_list()
    else:
        user_snps = db(db.SNP.user_id == auth.user_id).select(orderby=~db.SNP[attr]).as_list()

    # Return sorted list
    return dict(user_snps=user_snps)

def preprocess_file(file):
    rsids = []
    for line in file:
        line = line.decode('utf8')
        if not line.startswith("#"):
            data = line.split()
            rsids.append(data[0]+"\t"+data[3::][0])
            #rsids[data[0]] = data[3::][0]
    print(rsids[0:10])
    return rsids

@action('file_upload', method="PUT")
@action.uses(db, auth.user)
def file_upload():
    # This is the main file upload entrypoint when storing our files in memory
    uploaded_file = request.body # This is a file, you can read it.
    process_snps(preprocess_file(uploaded_file))
    return "ok"

def process_snps(file):
    SEARCH_REGEX = r"(rs\d+)\s+(\d+)\s+(\d+)\s+([ATGC])\s*([ATGC])"
    i = 0
    for line in file:
        i += 1
        #line = line.decode('utf8')
        rsid = ""
        allele1 = ""
        allele2 = ""
        result = re.search(SEARCH_REGEX, line)
        if result is None:
            entry = line.replace("\n", "").replace("\r", "").split("\t")
            rsid = entry[0]
            try:
                if len(entry[1]) == 2:
                    allele1 = entry[1][0]
                    allele2 = entry[1][1]
            except Exception as e:
                print("EXCEPTION:", e)
                print("ENTRIES:", entry)

        if i%10000 == 0:
            print(f"now processing line number {i}")
            print("line:", line)
            print("result:", result)
            print("rsid:", rsid, " allele1:", allele1, " allele2:", allele2)
            #print(opensnp_data['rs6684865'])
        
        if result or allele1 != "":
            if rsid == "":
                rsid = result.group(1)
                #chromosome = result.group(2)
                #position = result.group(3)
                allele1 = result.group(4)
                allele2 = result.group(5)
            #print(f"rsid:{rsid}|chromosome:{chromosome}|position:{position}|allele1{allele1}|allele2{allele2}")

            # NOTE: this db insert is very costly; without this line a 600k line file takes 10 seconds to process
            if rsid in opensnp_data and allele1 != "-" and allele2 != "-":
                #print("entered for rsid:", rsid)
                weight_of_evidence = opensnp_data[rsid]['weight_of_evidence']
                url = opensnp_data[rsid]['url']

                traits = {}

                summary = ""

                for each in opensnp_data[rsid]["annotations"]["snpedia"]:
                    traits[each["url"][-4] + each["url"][-2]] = each["summary"][0:len(each["summary"])]
                if len(traits) != 0:
                    #print("traits:", traits)
                    #print("Alleles:", allele1 + allele2)
                    for key in traits:
                        if key in complement(allele1+allele2):
                            #print(traits[key])
                            summary = traits[key]
                            allele1 = key[0]
                            allele2 = key[1]
                rsid = str(rsid.strip().replace("\n", ""))

                if summary != "":
                  db.SNP.update_or_insert(
                      (db.SNP.user_id == get_user_id()) & (db.SNP.rsid == rsid) & (db.SNP.allele1 == allele1) & (db.SNP.allele2 == allele2),
                      summary=summary,
                      url=url, 
                      rsid=rsid, 
                      allele1=allele1, 
                      allele2=allele2, 
                      weight_of_evidence=weight_of_evidence
                  )
    print("finished processing SNPS!")

################
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

    file = nqgcs.read(BUCKET, file_path)
    file = preprocess_file(str(file))
    process_snps(file)

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
            if USE_GCS:
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

# End GCS Handlers
##################