# myfavorites.py

from flask import Blueprint, render_template, current_app, _request_ctx_stack
from datetime import datetime, timedelta
from bson.json_util import dumps
from loguru import logger
import traceback
from ..utils import db
from ..utils.auth_utils import requires_auth

blueprint = Blueprint('myfavorites', __name__)
@blueprint.route("/v3/myfavs/<amount>", methods=["GET"], defaults={"page": 1})
@blueprint.route("/v3/myfavs/<amount>/<page>")
@requires_auth
def v3_myfavs(amount, page):
    current_user = _request_ctx_stack.top.current_user
    user_id = int(current_user["sub"].split("|")[2])
    
    try:
        with db.get_database() as client:
            r = list(client.database.pins.aggregate([
                {"$match" : {"user_id" : user_id}},
                {"$sort": {"pinned_on": -1}},
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
                {"$addFields": {
                    "pinned": True
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
                ]))
            
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