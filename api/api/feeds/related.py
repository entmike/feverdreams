# related.py

from flask import Blueprint, render_template, current_app, _request_ctx_stack, request
from datetime import datetime, timedelta
from bson.json_util import dumps
from loguru import logger
import traceback
from ..utils import db
from ..utils.auth_utils import supports_auth

blueprint = Blueprint('related', __name__)
@blueprint.route("/v3/related/<uuid>/<amount>", methods=["GET"], defaults={"page": 1})
@blueprint.route("/v3/related/<uuid>/<amount>/<page>")
@supports_auth
def v3_related(uuid, amount, page):
    current_user = _request_ctx_stack.top.current_user
    if current_user:
        user_id = int(current_user["sub"].split("|")[2])
    else:
        user_id = None

    with db.get_database() as client:
        piece = client.database.pieces.find_one({"uuid" : uuid})
        if piece:
            prompt_hash = piece.get("prompt_hash")

    args = request.args   
    q = {
        "prompt_hash": prompt_hash,
        "status" : "complete",
        "uuid" : {"$ne" : uuid},
        "nsfw": {"$nin": [True]},
        "hide": {"$nin": [True]},
    }
    
    if(args.get("hide")=="include"):
        del q["hide"]

    if(args.get("nsfw")=="include"):
        del q["nsfw"]

    if(args.get("nsfw")=="only"):
        q["nsfw"] = True

    with db.get_database() as client:
        operations = [
            {"$match": q},
            {"$sample": {"size": int(amount)}},
            {"$addFields":{
                "likes": "$pins"
            }},
            {"$lookup": {"from": "vw_users", "localField": "author", "foreignField": "user_id", "as": "userdets"}},
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
