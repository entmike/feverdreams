# undelete.py

from flask import Blueprint, render_template, current_app, _request_ctx_stack, request
from datetime import datetime, timedelta
from bson.json_util import dumps
from loguru import logger
import traceback
from ..utils import db, undelete_piece
from ..utils.auth_utils import requires_auth, requires_vetting

blueprint = Blueprint('undelete', __name__)

@blueprint.route("/undelete/<uuid>", methods=["POST"])
@requires_auth
@requires_vetting
def undelete(uuid):
    current_user = _request_ctx_stack.top.current_user
    discord_id = int(current_user["sub"].split("|")[2])
    with db.get_database() as client:
        piece = client.database.deleted_pieces.find_one({
            "uuid":uuid,
            "author": discord_id
        })
        if piece:
            piece["timestamp_completed"] = datetime.utcnow()
            piece["deleted"] = False
            if request.method == "POST":
                try:
                    dest = client.database.reviews.find_one({ "uuid":uuid, "author": discord_id })
                    undelete_piece(author = discord_id, uuid = uuid)
                    message = f"✅ Undeleted {uuid} for {discord_id}"
                    success = True
                except:
                    message = f"🪰 Could not undelete {uuid} for {discord_id}"
                    success = False
                return dumps({"success" : True, "message": message})
        else:
            return dumps({"success" : False, "message": "Could not undelete."})