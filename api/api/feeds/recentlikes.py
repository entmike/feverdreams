# recentlikes.py

from flask import Blueprint, render_template, current_app, _request_ctx_stack
from datetime import datetime, timedelta
from bson.json_util import dumps
from loguru import logger
import traceback
from ..utils import db
from ..utils.auth_utils import supports_auth

blueprint = Blueprint('recentlikes', __name__)

@blueprint.route("/v3/recentlikes/<amount>", methods=["GET"], defaults={"page": 1})
@blueprint.route("/v3/recentlikes/<amount>/<page>", methods=["GET"])
@supports_auth
def recent_likes(amount,page):
    # Horrible.  Merge with recent, you lazy MF.  -You, still later.
    current_user = _request_ctx_stack.top.current_user
    if current_user:
        user_id = int(current_user["sub"].split("|")[2])
    else:
        user_id = None
    try:
        with db.get_database() as client:
            operations = [
                {"$match" : {}},
                { "$group" :
                    {
                        "_id" : "$uuid",
                        "count" : { "$sum": 1 },
                        "pinned_on" : {"$last":"$pinned_on"}
                    }
                },
                {"$sort": {"pinned_on": -1}},
                {"$addFields":{
                    "uuid": "$_id"
                }},
                {"$skip": (int(page) - 1) * int(amount)},
                {"$limit": int(amount)},
                {"$lookup": {"from": "pieces", "localField": "uuid", "foreignField": "uuid", "as": "pieces"}},
                {"$unwind": {
                    "path": "$pieces",
                    "preserveNullAndEmptyArrays" : False
                }},
                {"$replaceRoot" : {
                    "newRoot": "$pieces"
                }},
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
            r = list(client.database.pins.aggregate(operations))
            # Strip private params out
            for piece in r:
                try:
                    if piece["private"] and piece["author"] != user_id:
                        del piece["params"]
                except:
                    pass

            return dumps(r)
    except:
        tb = traceback.format_exc()
        logger.error(tb)
        return dumps({
            "success" : False,
            "message" : "Delivery failed!",
            "traceback" : tb
        })