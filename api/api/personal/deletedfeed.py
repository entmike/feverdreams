# deletedfeed.py

from flask import Blueprint, render_template, current_app, _request_ctx_stack, request
from datetime import datetime, timedelta
from bson.json_util import dumps
from loguru import logger
import traceback
from ..utils import db, delete_piece
from ..utils.auth_utils import requires_auth, requires_vetting

blueprint = Blueprint('deletedfeed', __name__)

@blueprint.route("/v3/deletedfeed/<gallery_id>/<amount>", methods=["GET"], defaults={"page": 1})
@blueprint.route("/v3/deletedfeed/<gallery_id>/<amount>/<page>")
@requires_auth
@requires_vetting
def v3_deletedfeed(gallery_id, amount, page):
    current_user = _request_ctx_stack.top.current_user
    if current_user:
        user_id = int(current_user["sub"].split("|")[2])
    else:
        user_id = None

    if user_id != int(gallery_id):
        return dumps({"success" : False, "message" : "Wrong user."})

    q = {
        "author_id": int(gallery_id),
        "status" : "complete"
    }

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
                "likes": "$pins",
                "deleted" : True
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
        
        r = list(client.database.deleted_pieces.aggregate(operations))

        # Strip private params out
        for piece in r:
            try:
                if piece["private"] and piece["author"] != user_id:
                    del piece["params"]
            except:
                pass
        
        return dumps(r)