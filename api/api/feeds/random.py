# random.py

from flask import Blueprint, render_template, current_app, _request_ctx_stack
from datetime import datetime, timedelta
from bson.json_util import dumps
from loguru import logger
import traceback
from ..utils import db
from ..utils.auth_utils import supports_auth

blueprint = Blueprint('random', __name__)
@blueprint.route("/random/<type>/<amount>", methods=["GET"])
@supports_auth
def v3_random(type, amount):
    user_info = _request_ctx_stack.top.user_info
    if user_info:
        user_id = int(user_info["user_id"].split("|")[2])
    else:
        user_id = None

    q = {
        "nsfw": {"$nin": [True]},
        "hide": {"$nin": [True]},
        "origin": "web",
        "thumbnails" : {"$exists" : True}
    }
    if type == "disco":
        q["algo"] = {"$ne" : "stable"}
    
    if type == "stable":
        q["algo"] = "stable"
        q["origin"] = "web"

    if type == "dream":
        q["algo"] = "stable"
        q["origin"] = "dream"


    with db.get_database() as client:
        operations = [
            {"$match": q},
            {"$sample": {"size": int(amount)}},
            {"$lookup": {"from": "vw_users", "localField": "author", "foreignField": "user_id", "as": "userdets"}},
            {"$unwind": {
                "path": "$userdets",
                "preserveNullAndEmptyArrays" : True
            }},
            {"$addFields": {"userdets.user_str": {"$toString": "$userdets.user_id"}}}
        ]
        if user_id:
            operations.append({
            "$lookup" : {
                "from": "pins",
                "let": {
                    "user": user_id,
                    "uuid" : "$uuid"
                },
                "pipeline": [{
                    "$match": {
                        "$and": [
                            {"$expr": {"$eq": ['$user_id', '$$user'] }},
                            {"$expr": {"$eq": ['$uuid', '$$uuid'] }},
                        ]
                    }
                }],
                "as": "pinned"
            }})
            operations.append({
                "$unwind" : {
                    "path": "$pinned",
                    "includeArrayIndex": 'string',
                    "preserveNullAndEmptyArrays": True
                }
            })
        r = list(client.database.pieces.aggregate(operations))
        # Strip private params out
        for piece in r:
            try:
                if piece["private"] and piece["author"] != user_id:
                    del piece["params"]
            except:
                pass


        return dumps(r)
