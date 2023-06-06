"""
This file defines the database models
"""

import datetime
import random
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

db.commit()

#db.SNP.truncate()