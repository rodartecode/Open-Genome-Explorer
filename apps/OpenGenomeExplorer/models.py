"""
This file defines the database models
"""

import datetime
import random
import json
from py4web.utils.populate import FIRST_NAMES, LAST_NAMES, IUP
from .common import db, Field, auth
from pydal.validators import *


def get_user_email():
    return auth.current_user.get('email') if auth.current_user else None

def get_username():
    return auth.current_user.get('username') if auth.current_user else None

def get_user_id():
    return auth.current_user.get('id') if auth.current_user else None

def get_time():
    return datetime.datetime.utcnow().isoformat()


### Define your table below
#
# db.define_table('thing', Field('name'))
#
## always commit your models to avoid problems later

db.define_table(
    "SNP",
    Field('username', 'string', default=get_username),
    Field('url', 'string'),
    Field('rsid', 'string', requires=IS_NOT_EMPTY()),
    Field('allele1', 'string', requires=IS_NOT_EMPTY()),
    Field('allele2', 'string', requires=IS_NOT_EMPTY()),
    Field('summary', 'text'),
    Field('weight_of_evidence', 'integer'),
    Field('user_id', 'reference auth_user', default=get_user_id),
    auth.signature
)

db.define_table(
    "SNP_File",
    Field('owner', default=get_user_email),
    Field('file_name'),
    Field('file_type'),
    Field('file_date'),
    Field('file_path'),
    Field('file_size', 'integer'),
    Field('confirmed', 'boolean', default=False))

db. define_table(
    "RSID",
    Field('rsid', 'string', requires=IS_NOT_EMPTY()),
    Field('last_updated', 'datetime', default=get_time),
)

db.define_table(
    "RSID_Info",
    Field('rsid', 'reference RSID'),
    Field('url', 'string'),
    Field('allele1', 'string'),
    Field('allele2', 'string'),
    Field('summary', 'text'),
    Field('weight_of_evidence', 'integer'),
    Field('last_updated', 'datetime', default=get_time),
)

db.commit()

#db.SNP.truncate()
import re

def extract_final_pair(url):
    match = re.search(r'\(([^)]+)\)$', url)
    if match:
        # Removing the semicolon and joining the characters.
        return match.group(1).split(';')
    else:
        return None


def init_db():
    with open('good_snp_data.json', 'r') as f:
        good_snps = json.load(f)
    for rsid, info in good_snps:
        inserted_rsid = db.RSID.update_or_insert(rsid=rsid)
        if inserted_rsid:
            for entry in info["snpedia"]:
                url = entry["url"]
                summary = entry["summary"]
                allele1, allele2 = extract_final_pair(url)
                new_info = dict(url=url, allele1=allele1, allele2=allele2, summary=summary)
                db.RSID_Info.insert(rsid=inserted_rsid, **new_info)

# Used for testing; clears SNP data
def clear_db():
    db(db.SNP).delete()
    db.commit()