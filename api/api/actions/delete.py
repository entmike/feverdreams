# delete.py

from flask import Blueprint, render_template, current_app, _request_ctx_stack, request
from datetime import datetime, timedelta
from bson.json_util import dumps
from loguru import logger
import traceback
from ..utils import db, delete_piece
from ..utils.auth_utils import requires_auth, requires_vetting

blueprint = Blueprint('delete', __name__)

@blueprint.route("/delete/<uuid>", methods=["POST"])
@requires_auth
@requires_vetting
def delete(uuid):
    current_user = _request_ctx_stack.top.current_user
    discord_id = int(current_user["sub"].split("|")[2])
    with db.get_database() as client:
        piece = client.database.all_pieces.find_one({
            "uuid":uuid,
            "author": discord_id
        })
        if piece:
            if request.method == "POST":
                try:
                    delete_piece(author = discord_id, uuid = uuid)
                    message = f"✅ Deleted {uuid} for {discord_id}"
                    success = True
                except:
                    message = f"🪰 Could not delete {uuid} for {discord_id}"
                    success = False
                return dumps({"success" : success, "message": message})
        else:
            return dumps({"success" : False, "message": "Could not delete."})