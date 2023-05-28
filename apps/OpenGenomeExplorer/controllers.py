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

# Some constants.
MAX_RETURNED_USERS = 20 # Our searches do not return more than 20 users.
MAX_RESULTS = 20 # Maximum number of returned meows. 

url_signer = URLSigner(session)

@action('index')
@action.uses('index.html', url_signer, db, auth.user)
def index():

    post_meow_url = URL('post_meow', signer=url_signer)
    post_reply_url = URL('post_reply', signer=url_signer)
    get_meows_url = URL('get_meows', signer=url_signer)
    get_user_meows_url = URL('get_user_meows', signer=url_signer)
    get_recent_meows_url = URL('get_recent_meows', signer=url_signer)
    your_meows_url = URL('your_meows', signer=url_signer)
    get_replies_url = URL('get_replies', signer=url_signer)
    set_follow_url = URL('set_follow', signer=url_signer)
    search_url = URL('search', signer=url_signer)
    auth_verify_url = URL('auth_verify', signer=url_signer)
    get_snps_url = URL('get_SNPs', signer=url_signer)
    file_upload_url = URL('file_upload', signer=url_signer)

    #print("Meow URL:", get_meows_url)
    return dict(file_upload_url=file_upload_url, get_snps_url=get_snps_url, auth_verify_url=auth_verify_url, get_recent_meows_url=get_recent_meows_url, get_user_meows_url=get_user_meows_url, your_meows_url=your_meows_url,get_replies_url=get_replies_url, post_reply_url=post_reply_url, get_meows_url=get_meows_url, post_meow_url=post_meow_url, set_follow_url=set_follow_url, search_url=search_url)

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
    first = True

    # TODO: Remember to process the raw file first, this doesn't do that yet
    # TODO: Issue with full length
    for line in file.split("\n")[0:100]:
        try:
            split_line = line.split("\t")
            if first:
                #print("split_line:",split_line)
                first = False
            rsid = split_line[0]
            alleles = split_line[1]
            if (alleles != "--"):
                allele1 = alleles[0]
                allele2 = alleles[1]
                db.SNP.insert(rsid=rsid, allele1=allele1, allele2=allele2)
        except Exception as e:
            print(e)

    return "ok"

@action('search')
@action.uses(url_signer.verify(), db, auth.user)
def search():
    q = request.params.get("q")
    print("q:", q)
    user_rows = []
    if q:
        user_rows = db(db.auth_user.username.contains(q)).select(db.auth_user.username, db.auth_user.id, limitby=(0, MAX_RETURNED_USERS)).as_list()
    else:
        user_rows = db(db.auth_user).select(db.auth_user.username, db.auth_user.id, limitby=(0, MAX_RETURNED_USERS)).as_list()

    #print("user rows:", user_rows)
    follow_rows = db(db.follow.follower == auth.user_id).select(db.follow.followee, limitby=(0, MAX_RETURNED_USERS)).as_list()
    users = {}
    for user in user_rows:
        users[user['id']] = {"follow":"Follow", "color":"button is-success is-outlined", "icon":"fa fa-check", 'username':user['username'], "id":user['id']}
        for followee in follow_rows:
            if user['id'] == followee['followee']:
                users[user['id']] = {"follow":"Unfollow", "color":"button is-danger is-outlined", "icon":"fa fa-times", 'username':user['username'], "id":user['id']}
    #print(users)
    users = list(users.values())
    print("list of users:", users)
    return dict(user_rows=users)

@action('post_meow')
@action.uses(url_signer.verify(), db, auth.user)
def post_meow():
    m = request.params.get("m")
    db.meow.insert(content=m)
    print(m)

@action('post_reply')
@action.uses(url_signer.verify(), db, auth.user)
def post_reply():
    reply = request.params.get("reply")
    meow_id = request.params.get("meow_id")
    db.reply.insert(content=reply, meow_id=meow_id)
    print(reply)

@action('get_replies')
@action.uses(url_signer.verify(), db, auth.user)
def get_replies():
    meow_id = request.params.get("meow_id")
    assert meow_id is not None
    reply_rows = db(db.reply.meow_id == meow_id).select(db.reply.author, db.reply.replies, db.reply.timestamp, db.reply.content, db.auth_user.id, db.reply.id, join=db.auth_user.on(db.reply.author == db.auth_user.username)).as_list()
    #follow_rows = db(db.follow.follower == auth.user_id).select(db.follow.followee).as_list()
    replies = []
    for reply in reply_rows:
        replies.append({'author':reply['reply']['author'], 'replies':reply['reply']['replies'], 'timestamp':reply['reply']['timestamp'], 'content':reply['reply']['content'], "user_id":reply['auth_user']['id'], "id":reply['reply']['id']})
        #print(meow)
    replies = replies[::-1]
    while len(replies) > MAX_RESULTS:
        replies.pop()
    #print(meows)
    #print("Meow Rows:", meow_rows)
    return dict(replies=replies)

@action('your_meows')
@action.uses(url_signer.verify(), db, auth.user)
def your_meows():
    meow_rows = db(db.meow.author == get_username()).select(db.meow.author, db.meow.replies, db.meow.timestamp, db.meow.content, db.auth_user.id, db.meow.id, join=db.auth_user.on(db.meow.author == db.auth_user.username)).as_list()
    #follow_rows = db(db.follow.follower == auth.user_id).select(db.follow.followee).as_list()
    meows = []
    for meow in meow_rows:
        meows.append({'author':meow['meow']['author'], 'replies':meow['meow']['replies'], 'timestamp':meow['meow']['timestamp'], 'content':meow['meow']['content'], "user_id":meow['auth_user']['id'], "id":meow['meow']['id']})
        #print(meow)
    meows = meows[::-1]
    while len(meows) > MAX_RESULTS:
        meows.pop()
    #print(meows)
    #print("Meow Rows:", meow_rows)
    return dict(meows=meows)

@action('get_user_meows')
@action.uses(url_signer.verify(), db, auth.user)
def get_user_meows():
    user_id = int(request.params.get("user_id"))
    assert user_id is not None

    meow_rows = db(db.meow).select(db.meow.author, db.meow.replies, db.meow.timestamp, db.meow.content, db.auth_user.id, db.meow.id, join=db.auth_user.on(db.meow.author == db.auth_user.username)).as_list()
    #follow_rows = db(db.follow.follower == auth.user_id).select(db.follow.followee).as_list()
    meows = []
    for meow in meow_rows:
        if int(meow['auth_user']['id']) == user_id:
            meows.append({'author':meow['meow']['author'], 'replies':meow['meow']['replies'], 'timestamp':meow['meow']['timestamp'], 'content':meow['meow']['content'], "user_id":meow['auth_user']['id'], "id":meow['meow']['id']})
        #print(meow)
    meows = meows[::-1]
    while len(meows) > MAX_RESULTS:
        meows.pop()
    #print("Meow Rows:", meow_rows)
    return dict(meows=meows)

@action('get_recent_meows')
@action.uses(url_signer.verify(), db, auth.user)
def get_user_meows():

    meow_rows = db(db.meow).select(db.meow.author, db.meow.replies, db.meow.timestamp, db.meow.content, db.auth_user.id, db.meow.id, join=db.auth_user.on(db.meow.author == db.auth_user.username)).as_list()
    #follow_rows = db(db.follow.follower == auth.user_id).select(db.follow.followee).as_list()
    meows = []
    for meow in meow_rows:
        meows.append({'author':meow['meow']['author'], 'replies':meow['meow']['replies'], 'timestamp':meow['meow']['timestamp'], 'content':meow['meow']['content'], "user_id":meow['auth_user']['id'], "id":meow['meow']['id']})
        #print(meow)
    meows = meows[::-1]
    while len(meows) > MAX_RESULTS:
        meows.pop()
    #print("Meow Rows:", meow_rows)
    return dict(meows=meows)

@action('get_meows')
@action.uses(url_signer.verify(), db, auth.user)
def get_meows():
    meow_rows = db(db.meow).select(db.meow.author, db.meow.replies, db.meow.timestamp, db.meow.content, db.auth_user.id, db.meow.id, join=db.auth_user.on(db.meow.author == db.auth_user.username)).as_list()
    #follow_rows = db(db.follow.follower == auth.user_id).select(db.follow.followee).as_list()
    meows = []
    for meow in meow_rows:
        if len(db((db.follow.followee == meow['auth_user']['id'])).select().as_list()) != 0 or meow['auth_user']['id'] == auth.user_id:
            meows.append({'author':meow['meow']['author'], 'replies':meow['meow']['replies'], 'timestamp':meow['meow']['timestamp'], 'content':meow['meow']['content'], "user_id":meow['auth_user']['id'], "id":meow['meow']['id']})
        #print(meow)
    meows = meows[::-1]
    while len(meows) > MAX_RESULTS:
        meows.pop()
    #print(meows)
    #print("Meow Rows:", meow_rows)
    return dict(meows=meows)

@action("get_users")
@action.uses(db, auth.user)
def get_users():
    # Implement. Lists all the users 
    rows = db(db.auth_user).select(db.auth_user.username, limitby=(0, MAX_RETURNED_USERS))
    for row in rows:
        print(row['username'])
    return dict(rows=rows)

@action("set_follow", method=["GET", "POST"])
@action.uses(url_signer.verify(), db, auth.user)
def set_follow():
    user_id = request.params.get("user_id")
    assert user_id is not None
    
    print("selected user ID:", user_id, "my user id:", auth.user_id)

    if len(db((db.follow.follower==auth.user_id) & (db.follow.followee==user_id)).select()) == 0:
        print("it's not in there")
        db.follow.insert(follower=auth.user_id, followee=user_id)
    else:
        db((db.follow.follower==auth.user_id) & (db.follow.followee==user_id)).delete()

    redirect(URL('index'))