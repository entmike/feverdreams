# follow.py

from flask import Blueprint, render_template, current_app, _request_ctx_stack, request
from datetime import datetime, timedelta
from bson.json_util import dumps
from loguru import logger
import traceback
from ..utils import db
from ..utils.auth_utils import requires_auth

blueprint = Blueprint('follow', __name__)

@blueprint.route("/follow/<follow_id>", methods=["GET","POST","DELETE"])
@requires_auth
def follow(follow_id):
    current_user = _request_ctx_stack.top.current_user
    discord_id = int(current_user["sub"].split("|")[2])

    if request.method == "DELETE":
        with db.get_database() as client:
            client.database.get_collection("follows").delete_one({"user_id": discord_id, "follow_id" : int(follow_id)})
        
        return dumps({
            "message": "Unfollowed",
            "success" : True
        })

    if request.method == "POST":
        with db.get_database() as client:
            client.database.get_collection("follows").update_one({"user_id": discord_id, "follow_id" : int(follow_id)}, {
                "$set": {
                    "user_id": discord_id,
                    "followed_on": datetime.utcnow(),
                    "follow_id": int(follow_id)
                }
            }, upsert=True)
        
        return dumps({
            "message" : "Followed",
            "success" : True
        })

    if request.method == "GET":
        with db.get_database() as client:
            follow = client.database.get_collection("follows").find_one({"user_id": discord_id, "follow_id" : int(follow_id)})
            if follow:
                following = True
            else:
                following = False
        
        return dumps({"following": following})