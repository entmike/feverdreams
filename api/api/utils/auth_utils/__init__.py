from flask import current_app
from ..db import get_database
from functools import wraps
from flask import request
from jose import jwt
from urllib.request import urlopen
from loguru import logger
import json
from bson.json_util import dumps
from json import loads
from flask import _request_ctx_stack
from datetime import datetime

import http.client
import os, sys
import urllib.parse

access_token_timestamp = None
access_token = None

AUTH0_ALGORITHMS = ["RS256"]

usercache = {}
permissioncache = {}

def my_permissions():
    current_user = _request_ctx_stack.top.current_user
    # User Permissions
    path = f"/api/v2/users/{urllib.parse.quote(current_user['sub'])}/permissions"
    conn = http.client.HTTPSConnection(current_app.config["AUTH0_DOMAIN"])
    conn.request("GET", path, headers={
        'authorization': f"Bearer {get_access_token()}"
    })
    res = conn.getresponse()
    data = res.read()
    perms=loads(data.decode("utf-8"))
    return perms
    
def requires_permission(f):
    """Determines if the required scope is present in the Access Token
    Args:
        required_scope (str): The scope required to access the resource
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        print(kwargs)
        current_user = _request_ctx_stack.top.current_user
        # logger.info(f"🔏 Checking {current_user['sub']} for permissions '{perm}'...")
        try:
            if current_user['sub'] in permissioncache:
                for permission in permissioncache[current_user['sub']]:
                    # logger.info(permission)
                    if permission["permission_name"] == perm:
                        # logger.info(f"🔐 Permission {perm} found.")
                        return True
            else:
                return False
        except:
            return False
    
    return decorated

def requires_vetting(f):
    """Determines if the Access Token is valid and user is vetted"""
    @wraps(f)
    def decorated(*args, **kwargs):
        user_pass = _request_ctx_stack.top.user_pass
        if not user_pass:
            raise AuthError({"code": "not_vetted", "description": "You may not use this API until your user account is vetted."}, 401)
        else:
            return f(*args, **kwargs)
    return decorated

def requires_auth(f):
    """Determines if the Access Token is valid"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_token_auth_header()
        jsonurl = urlopen("https://" + current_app.config["AUTH0_DOMAIN"] + "/.well-known/jwks.json")
        jwks = json.loads(jsonurl.read())
        unverified_header = jwt.get_unverified_header(token)
        rsa_key = {}
        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = {"kty": key["kty"], "kid": key["kid"], "use": key["use"], "n": key["n"], "e": key["e"]}
        if rsa_key:
            try:
                payload = jwt.decode(token, rsa_key, algorithms=AUTH0_ALGORITHMS, audience=current_app.config["AUTH0_API_AUDIENCE"], issuer="https://" + current_app.config["AUTH0_DOMAIN"] + "/")
            except jwt.ExpiredSignatureError:
                raise AuthError({"code": "token_expired", "description": "token is expired"}, 401)
            except jwt.JWTClaimsError:
                raise AuthError({"code": "invalid_claims", "description": "incorrect claims, please check the audience and issuer"}, 401)
            except Exception:
                raise AuthError({"code": "invalid_header", "description": "Unable to parse authentication token."}, 401)

            _request_ctx_stack.top.current_user = payload
            user_info = user_pulse(payload, True)
            if user_info:
                if "banned" in user_info:
                    logger.info(f"🔨 Banned user attempt from: {user_info}")
                    if user_info["banned"] == True:
                        raise AuthError({"code": "banned", "description": "User is banned from API"}, 401)
            
                if "pass" not in user_info or user_info["pass"] == False:
                    logger.info(f"🆕 New user attempt from: {user_info}")
                    user_pass = False
                else:
                    user_pass = True
            else:
                user_pass = False

            _request_ctx_stack.top.user_info = user_info
            _request_ctx_stack.top.user_pass = user_pass
            # logger.info(f"👤 {user_info}")

            return f(*args, **kwargs)
        raise AuthError({"code": "invalid_header", "description": "Unable to find appropriate key"}, 401)

    return decorated

def supports_auth(f):
    """Determines if the Access Token is valid"""
    @wraps(f)
    def decorated(*args, **kwargs):
        jsonurl = urlopen("https://" + current_app.config["AUTH0_DOMAIN"] + "/.well-known/jwks.json")
        jwks = json.loads(jsonurl.read())
        _request_ctx_stack.top.current_user = None
        _request_ctx_stack.top.user_info = None
        try:
            token = get_token_auth_header()
            unverified_header = jwt.get_unverified_header(token)            
        except:
            # logger.info(f"👤 Unauthenticated request, allowing.")
            return f(*args, **kwargs)

        rsa_key = {}
        user_info = None
        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = {"kty": key["kty"], "kid": key["kid"], "use": key["use"], "n": key["n"], "e": key["e"]}
        if rsa_key:
            try:
                payload = jwt.decode(token, rsa_key, algorithms=AUTH0_ALGORITHMS, audience=current_app.config["AUTH0_API_AUDIENCE"], issuer="https://" + current_app.config["AUTH0_DOMAIN"] + "/")
                _request_ctx_stack.top.current_user = payload
                user_info = user_pulse(payload, True)
                _request_ctx_stack.top.user_info = user_info
            except jwt.ExpiredSignatureError:
                pass
                # raise AuthError({"code": "token_expired", "description": "token is expired"}, 401)
            except jwt.JWTClaimsError:
                pass
                # raise AuthError({"code": "invalid_claims", "description": "incorrect claims, please check the audience and issuer"}, 401)
            except Exception:
                pass
                # raise AuthError({"code": "invalid_header", "description": "Unable to parse authentication token."}, 401)

        # logger.info(f"👤 {user_info}")
        return f(*args, **kwargs)

        # raise AuthError({"code": "invalid_header", "description": "Unable to find appropriate key"}, 401)
    return decorated

# Error handler
class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code

# Format error response and append status code
def get_token_auth_header():
    """Obtains the Access Token from the Authorization Header"""
    auth = request.headers.get("Authorization", None)
    if not auth:
        raise AuthError({"code": "authorization_header_missing", "description": "Authorization header is expected"}, 401)

    parts = auth.split()

    if parts[0].lower() != "bearer":
        raise AuthError({"code": "invalid_header", "description": "Authorization header must start with" " Bearer"}, 401)
    elif len(parts) == 1:
        raise AuthError({"code": "invalid_header", "description": "Token not found"}, 401)
    elif len(parts) > 2:
        raise AuthError({"code": "invalid_header", "description": "Authorization header must be" " Bearer token"}, 401)

    token = parts[1]
    return token

def get_auth0_mgmt_token():
    conn = http.client.HTTPSConnection(current_app.config["AUTH0_DOMAIN"])
    payload = dumps({
        "client_id":current_app.config["AUTH0_MGMT_API_CLIENT_ID"],
        "client_secret":current_app.config["AUTH0_MGMT_API_SECRET"],
        "audience":f"https://{current_app.config['AUTH0_DOMAIN']}/api/v2/",
        "grant_type":"client_credentials"
    })
    headers = { 'content-type': "application/json" }
    conn.request("POST", "/oauth/token", payload, headers)
    res = conn.getresponse()
    data = res.read()
    return loads(data.decode("utf-8"))

def user_pulse(current_user, update_db):
    # logger.info(f"💓 User activity from {current_user['sub']}")
    discord_id = int(current_user["sub"].split("|")[2])
    user_info = {}
    if current_user['sub'] in usercache:
        user_info = usercache[current_user['sub']]
    else:
        with get_database() as client:
            u = client.database.users.find_one({
                "user_id": discord_id
            })
            # If user info not in DB....
            if not u or not u.get("user_info"):
                # logger.info(f"🌍 Looking up {current_user['sub']}...")
                path = f"/api/v2/users/{urllib.parse.quote(current_user['sub'])}"
                conn = http.client.HTTPSConnection(current_app.config["AUTH0_DOMAIN"])
                logger.info(get_access_token())
                conn.request("GET", path, headers={
                    'authorization': f"Bearer {get_access_token()}"
                })
                res = conn.getresponse()
                data = res.read()
                user_info=loads(data.decode("utf-8"))
                
                # Error if token expired.
                if "error" not in user_info:
                    try:
                        nickname = user_info["nickname"]
                        picture = user_info["picture"]
                    except:
                        nickname = "Unknown"
                        picture = "Unknown"
                    
                    # logger.info(f"📅 Updating user")
                    client.database.users.update_one({
                        "user_id": discord_id
                    }, {
                        "$set": {
                            "user_info" : user_info,
                            "last_seen": datetime.utcnow(),
                            "nickname": nickname,
                            "picture": picture
                        }
                    },
                    upsert=True)
            else:
                # logger.info(f"Already have user metadata for {current_user['sub']}")
                user_info = u.get("user_info")

        
        if "error" not in user_info:
            # User Permissions
            # logger.info(f"🌍 Looking up permissions for {current_user['sub']}...")
            path = f"/api/v2/users/{urllib.parse.quote(current_user['sub'])}/permissions"
            conn = http.client.HTTPSConnection(current_app.config["AUTH0_DOMAIN"])
            conn.request("GET", path, headers={
                'authorization': f"Bearer {get_access_token()}"
            })
            res = conn.getresponse()
            data = res.read()
            perms=loads(data.decode("utf-8"))
            permissioncache[current_user['sub']] = perms
        else:
            logger.info(user_info)
            user_info = None
            if current_user['sub'] in usercache:
                del usercache[current_user['sub']]
            if current_user['sub'] in permissioncache:
                del permissioncache[current_user['sub']]
        # except:
        #     import traceback
        #     tb = traceback.format_exc()
        #     user_info={}
        #     logger.error(tb)
        #     if current_user['sub'] in usercache:
        #         del usercache[current_user['sub']]
        #     if current_user['sub'] in permissioncache:
        #         del permissioncache[current_user['sub']]

    if user_info:
        with get_database() as client:
            u = client.database.users.find_one({
                "user_id": discord_id
            })
            if u:
                if u.get("banned") == True:
                    user_info["banned"] = True
                if u.get("pass") == True:
                    user_info["pass"] = True
                else:
                    user_info["pass"] = False
            
            usercache[current_user['sub']] = user_info
            

    return user_info

def get_access_token():
    try:
        t = access_token
    except:
        t = None
        
    if not t:
        access_token = get_auth0_mgmt_token()["access_token"]
        access_token_timestamp = datetime.utcnow()
    else:
        n = datetime.utcnow()
        duration = n - access_token_timestamp
        
        if duration > 60:
            access_token = get_auth0_mgmt_token()["access_token"]
            access_token_timestamp = datetime.utcnow()

    return access_token
