# -*- coding: utf-8 -*-

from flask import Flask
from flask import request
from flask import Response
import json
import MySQLdb
import sys
import hashlib

app = Flask(__name__)

def get_database():
    with open('credentials') as f:
        credentials = [x.strip().split(':') for x in f.readlines()]
    for ip, username, password, schema in credentials:
        return MySQLdb.connect(ip, username, password, schema)

#expand to check password later
def verify_user(username):
    db = get_database()
    cursor = db.cursor()
    sql = "SELECT * FROM user WHERE username = '%s'" % username
    try:
        cursor.execute(sql)
        user = cursor.fetchone()
        if user:
            db.close()
            return True
        else:
            db.close()
            print "Error: unable to find user"
            return False
    except:
        db.close()
        print "Error: unable to find user"
        return False

def authenticate_user(username, password):
    db = get_database()
    cursor = db.cursor()
    sql = "SELECT * FROM user WHERE username = '%s' AND password = '%s'" % (username, hashed_password(password))
    try:
        cursor.execute(sql)
        user = cursor.fetchone()
        if user:
            db.close()
            return True
        else:
            db.close()
            print "Error: unable to find user"
            return False
    except:
        db.close()
        print "Error: unable to find user"
        return False

def create_user(username, password):
    db = get_database()
    cursor = db.cursor()
    sql = "INSERT INTO user(username, password) VALUES ('%s', '%s')" % (username, hashed_password(password))
    try:
        cursor.execute(sql)
        db.commit()
        return True
    except:
        db.rollback()
        return False

def verify_session(db, session_id):
    cursor = db.cursor()
    sql = "SELECT * FROM session WHERE id = '%s'" % session_id
    try:
        cursor.execute(sql)
        user = cursor.fetchone()
        if user:
            return True
        else:
            print "Error: unable to find session"
            return False
    except:
        print "Error: unable to find session"
        return False

def insert_session(db, session_id, location_id, username):
    cursor = db.cursor()
    sql = "INSERT INTO session(id, location, userid) VALUES ('%s', '%s', '%s')" % (session_id, location_id, username)
    try:
        cursor.execute(sql)
        db.commit()
        return True
    except:
        db.rollback()
        return False

def insert_interest(db, session_id, keywords):
    cursor = db.cursor()
    sql = "INSERT INTO interest(sessionid) VALUES ('%s')" % session_id
    try:
        cursor.execute(sql)
        db.commit()
        interest_id = cursor.lastrowid
        for keyword in keywords:
            insert_keyword(db, interest_id, keyword)
        return True
    except:
        print "Unexpected error:", sys.exc_info()
        db.rollback()
        return False

def insert_keyword(db, interest_id, keyword):
    cursor = db.cursor()
    sql = "INSERT INTO interest_keyword(interestid, keyword) VALUES ('%d', '%s')" % (interest_id, keyword)
    try:
        cursor.execute(sql)
        db.commit()
        return True
    except:
        print "Unexpected error:", sys.exc_info()
        db.rollback()
        return False

def get_domain_id(db, domain_name):
    cursor = db.cursor()
    sql = "SELECT * FROM domain WHERE name = '%s'" % domain_name
    try:
        cursor.execute(sql)
        domain = cursor.fetchone()
        return domain[0]
    except:
        print "Error: unable to find domain"
        return None

def insert_domain(db, domain):
    cursor = db.cursor()
    sql = "INSERT INTO domain(name) VALUES ('%s')" % domain
    try:
        cursor.execute(sql)
        db.commit()
        return cursor.lastrowid
    except:
        print "Unexpected error:", sys.exc_info()
        db.rollback()
        return get_domain_id(db, domain)

def insert_domain_session(db, session_id, domain_id):
    cursor = db.cursor()
    sql = "INSERT INTO session_domain(sessionid, domainid) VALUES ('%s', '%d')" % (session_id, domain_id)
    try:
        cursor.execute(sql)
        db.commit()
        return True
    except:
        print "Unexpected error:", sys.exc_info()
        db.rollback()
        return False

def hashed_password(password):
    return hashlib.sha1(password).hexdigest()

@app.route('/interest/', methods=['POST'])
def handle_interest():
    interest = json.loads(request.form['interest'])
    user_id = request.form['userId']
    location_id = request.form['locationId']
    session_id = request.form['sessionId']
    db = get_database()
    if verify_user(user_id):
        insert_session(db, session_id, location_id, user_id)
        insert_interest(db, session_id, interest['interest'])
    db.close()
    return 'ok'

@app.route('/domain/', methods=['POST'])
def handle_domain():
    domain = request.form['domain']
    session_id = request.form['sessionId']
    db = get_database()
    if verify_session(db, session_id):
        try:
            domain_id = insert_domain(db, domain)
        finally:
            insert_domain_session(db, session_id, domain_id)
    db.close()
    return 'ok'

@app.route('/user/', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    if authenticate_user(username, password):
        return 'ok'
    return Response(
        'Bad credentials.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})

@app.route('/user/new', methods=['POST'])
def create_user_rest():
    username = request.form['username']
    password = request.form['password']
    if len(username) < 3 or len(password) < 5:
        return Response(
            'Username or password too short.', 400,
            {'WWW-Authenticate': 'Basic realm="Login Required"'})
    if verify_user(username):
        return Response(
            'User exists.', 400,
            {'WWW-Authenticate': 'Basic realm="Login Required"'})
    else:
        create_user(username, password)
        return 'ok'

@app.route('/test')
def compare_patterns():
    return "yey"


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)

