# review.py

from flask import Blueprint, render_template, current_app, _request_ctx_stack, request
from datetime import datetime, timedelta
from bson.json_util import dumps
from loguru import logger
import traceback
from ..utils import db, delete_piece
from ..utils.auth_utils import requires_auth, requires_vetting

blueprint = Blueprint('review', __name__)

@blueprint.route("/review/<uuid>", methods=["POST","DELETE"])
@requires_auth
@requires_vetting
def review(uuid):
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
                delete_piece(author = discord_id, uuid = uuid)
                message = f"♻️ Deleted {uuid} for {discord_id}"
            if request.method == "POST":
                client.database.pieces.insert_one(piece)
                client.database.discord_queue.insert_one(piece)
                client.database.reviews.delete_many({"author": discord_id, "uuid" : uuid})
                message = f"✅ Saved {uuid} for {discord_id}"
    
    return dumps({"success" : True, "message": message})