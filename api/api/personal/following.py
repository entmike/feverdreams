# following.py

from flask import Blueprint, render_template, current_app, _request_ctx_stack
from datetime import datetime, timedelta
from bson.json_util import dumps
from loguru import logger
import traceback
from ..utils import db
from ..utils.auth_utils import supports_auth, requires_auth

blueprint = Blueprint('following', __name__)
@blueprint.route("/following/feed/<amount>", methods=["GET"], defaults={"page": 1})
@blueprint.route("/following/feed/<amount>/<page>", methods=["GET"])
@requires_auth
def following_feed(amount, page):
    current_user = _request_ctx_stack.top.current_user
    discord_id = int(current_user["sub"].split("|")[2])
    logger.info(f"Request for following feed by {discord_id}...")

    with db.get_database() as client:
        follows = list(client.database.get_collection("follows").aggregate([
            {
                '$match': {
                    'user_id': discord_id
                }
            }
        ]))
        f = []
        for follow in follows:
            f.append(follow["follow_id"])
        logger.info(f)
        following = client.database.get_collection("pieces").aggregate([
            {
                '$match': {
                    'author': { "$in" : f},
                    "nsfw": {"$nin": [True]},
                    "hide": {"$nin": [True]},
                    "thumbnails" : {"$exists" : True},
                    "origin": "web",
                    "status" : "complete"
                }
            },
            {"$sort": {"timestamp_completed": -1}},
            {"$lookup": {"from": "vw_users", "localField": "author", "foreignField": "user_id", "as": "userdets"}},
            {"$skip": (int(page) - 1) * int(amount)},
            {"$limit": int(amount)},
            {"$unwind": {
                "path": "$userdets",
                "preserveNullAndEmptyArrays" : True
            }},
            {"$addFields": {"userdets.user_str": {"$toString": "$userdets.user_id"}}},
            ])
        following = list(following)
        for piece in following:
            try:
                if piece["private"] and piece["author"] != discord_id:
                    del piece["params"]
            except:
                pass

        return dumps(following)