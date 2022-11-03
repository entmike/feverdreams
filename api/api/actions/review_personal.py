# review_personal.py

from flask import Blueprint, render_template, current_app, _request_ctx_stack, request
from datetime import datetime, timedelta
from bson.json_util import dumps
from loguru import logger
import traceback
from ..utils import db, delete_piece
from ..utils.auth_utils import requires_auth, requires_vetting

blueprint = Blueprint('review_personal', __name__)

@blueprint.route("/review_personal/<uuid>", methods=["POST"])
@requires_auth
@requires_vetting
# @requires_permission
def review_personal(uuid):
    current_user = _request_ctx_stack.top.current_user
    discord_id = int(current_user["sub"].split("|")[2])
    with db.get_database() as client:
        piece = client.database.reviews.find_one({
            "uuid":uuid,
            "author": discord_id
        })
        if piece:
            piece["timestamp_completed"] = datetime.utcnow()
            if request.method == "DELETE":
                try:
                    client.database.deleted_pieces.insert_one(piece)
                except:
                    #probably a duplicate
                    pass
                client.database.reviews.delete_many({"author": discord_id, "uuid" : uuid})
                message = f"♻️ Deleted {uuid} for {discord_id}"
            if request.method == "POST":
                client.database.personal_pieces.insert_one(piece)
                client.database.reviews.delete_many({"author": discord_id, "uuid" : uuid})
                message = f"✅ Saved {uuid} for {discord_id}"   
    
    return dumps({"success" : True, "message": message})