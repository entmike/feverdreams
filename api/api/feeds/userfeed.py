# userfeed.py

from flask import Blueprint, render_template, current_app, _request_ctx_stack, request
from datetime import datetime, timedelta
from bson.json_util import dumps
from loguru import logger
import traceback
from ..utils import db
from ..utils.auth_utils import supports_auth

blueprint = Blueprint('userfeed', __name__)

@blueprint.route("/v3/userfeed/<gallery_id>/<amount>", methods=["GET"], defaults={"page": 1})
@blueprint.route("/v3/userfeed/<gallery_id>/<amount>/<page>")
@supports_auth
def v3_userfeed(gallery_id, amount, page):
    current_user = _request_ctx_stack.top.current_user
    if current_user:
        user_id = int(current_user["sub"].split("|")[2])
    else:
        user_id = None

    args = request.args
    include = []
    exclude = []
    try:
        include = args.get("include").split(",")
    except:
        pass
    try:
        exclude = args.get("exclude").split(",")
    except:
        pass
    # logger.info(exclude)
    # logger.info(include)
    q = {
        "author_id": int(gallery_id),
        "status" : "complete",
        "nsfw": {"$nin": [True]},
        "hide": {"$nin": [True]},
    }
    if 'hide' in include:
        del q["hide"]
    
    if 'nsfw' in include:
        del q["nsfw"]

    if 'dream' in exclude:
        q["origin"] = {"$nin": ["dream"]}

    with db.get_database() as client:
        operations = [
            {
                "$addFields": {"author_id": {"$toLong": "$author"}},
            },
            {"$match": q},
            {"$sort": {"_id": 1}},
            {"$sort": {"timestamp_completed": -1}},
            {"$skip": (int(page) - 1) * int(amount)},
            {"$limit": int(amount)},
            {"$addFields":{
                "likes": "$pins"
            }},
            {"$lookup": {"from": "vw_users", "localField": "author_id", "foreignField": "user_id", "as": "userdets"}},
            {"$unwind": {
                "path": "$userdets",
                "preserveNullAndEmptyArrays" : True
            }},
            {"$addFields": {"userdets.user_str": {"$toString": "$userdets.user_id"}}},
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