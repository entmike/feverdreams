# myinvites.py

import uuid
from flask import Blueprint, render_template, current_app, _request_ctx_stack, request
from datetime import datetime, timedelta
from bson.json_util import dumps
from loguru import logger
import traceback
from ..utils import db
from ..utils.auth_utils import requires_auth, requires_vetting

blueprint = Blueprint('myinvites', __name__)
@blueprint.route("/v3/myinvites", methods=["GET"])
@requires_auth
def myinvites():
    current_user = _request_ctx_stack.top.current_user
    discord_id = int(current_user["sub"].split("|")[2])
    with db.get_database() as client:
        invites = list(client.database.invites.aggregate([
            {"$match":{"user_id" : discord_id}},
            {"$lookup": {"from": "vw_users", "localField": "redeemed", "foreignField": "user_id", "as": "userdets"}},
            {"$unwind": {
                "path": "$userdets",
                "preserveNullAndEmptyArrays" : True
            }},
        ]))
        return dumps(invites)

@blueprint.route("/redeeminvite", methods=["POST"])
@requires_auth
def redeeminvite():
    current_user = _request_ctx_stack.top.current_user
    discord_id = int(current_user["sub"].split("|")[2])
    with db.get_database() as client:
        # Make sure user need invite
        u = client.database.users.find_one({
            "user_id": discord_id,
            "pass" : {"$ne":True}
        })
        # If user needs invite, proceed
        if u:
            # Get invite code
            invite_code = job = request.json.get("invite_code")
            # Invite code query
            q = {
                "invite_code" : invite_code,
                "redeemed" : {"$exists" : False}
            }
            # Find invite
            invite = client.database.invites.find_one(q)
            # If invite exists, proceed
            if invite:
                referrer = invite.get("user_id")
                # Mark user as vetted
                client.database.users.update_one({
                    "user_id": discord_id
                },{
                    "$set" : {
                        "pass" : True,
                        "referrer" : referrer
                    }
                })

                # Mark invite as used
                client.database.invites.update_one(q,{
                    "$set" : {
                        "redeemed" : discord_id,
                        "redeemed_timestamp" : datetime.utcnow()
                    }
                })
                return dumps({
                    "success" : True,
                    "invites" : "🥳 Welcome to Fever Dreams!"
                })
            else:
                # Invalid invite
                return dumps({
                    "success" : False,
                    "message" : "Invalid invite.  Please check your code."
                })
        else:
            # User already has invite
            return dumps({
                "success" : False,
                "message" : "You are already vetted.  Code not needed."
            })


@blueprint.route("/generateinvite", methods=["POST"])
@requires_auth
def generateinvite():
    current_user = _request_ctx_stack.top.current_user
    discord_id = int(current_user["sub"].split("|")[2])
    with db.get_database() as client:
        invites = 0
        u = client.database.users.find_one({
            "user_id": discord_id
        })
        if u:
            invites = u.get("invites")
            if invites and invites > 0:
                invites = invites - 1

                client.database.users.update_one({
                    "user_id": discord_id
                },{
                    "$set" : {"invites" : invites}
                })

                client.database.invites.insert_one({
                    "user_id": discord_id,
                    "invite_code" : str(uuid.uuid4()),
                    "timestamp" : datetime.utcnow()
                })

        return dumps({
            "success" : True,
            "invites" : invites
        })