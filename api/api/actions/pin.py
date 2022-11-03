# pin.py

from flask import Blueprint, render_template, current_app, _request_ctx_stack, request
from datetime import datetime, timedelta
from bson.json_util import dumps
from loguru import logger
import traceback
from ..utils import db
from ..utils.auth_utils import requires_auth

blueprint = Blueprint('pin', __name__)

@blueprint.route("/pin/<uuid>", methods=["POST","DELETE"])
@requires_auth
def pin(uuid):
    current_user = _request_ctx_stack.top.current_user
    if current_user:
        user_id = int(current_user["sub"].split("|")[2])
    else:
        user_id = None
    if request.method == "DELETE":
        with db.get_database() as client:
            client.database.pins.delete_many({"user_id": user_id, "uuid" : uuid})
            message = f"📌 Unpinned {uuid} for {user_id}"

    if request.method == "POST":
        with db.get_database() as client:
            client.database.pins.update_one({
                    "user_id": user_id,
                    "uuid" : uuid
                }, {
                "$set": {
                    "pinned_on": datetime.utcnow(),
                    "uuid": uuid
                }
            }, upsert=True)
            message = f"📌 Pinned {uuid} for {user_id}"
    
    with db.get_database() as client:
        # Update counts
        count = len(list(client.database.pins.aggregate([
            {"$match":{"uuid" : uuid}}
        ])))
        client.database.pieces.update_many({
            "uuid" : uuid
        }, {
            "$set": {
                "pins" : count
            }
        })

    return dumps({"success" : True, "message": message})