# tosagree.py

from flask import Blueprint, render_template, current_app, _request_ctx_stack, request
from datetime import datetime, timedelta
from bson.json_util import dumps
from loguru import logger
import traceback
from ..utils import db, undelete_piece
from ..utils.auth_utils import requires_auth, requires_vetting

blueprint = Blueprint('tosagree', __name__)

@blueprint.route("/v3/tosagree", methods=["POST"])
@requires_auth
def tosagree():
    user_info = _request_ctx_stack.top.user_info
    current_user = _request_ctx_stack.top.current_user
    user_id = int(current_user["sub"].split("|")[2])
    tos_uuid = request.json.get("uuid")
    with db.get_database() as client:
        client.database.users.update_many({
            "user_id" : user_id
        },{
            "$set" : {
                "tos_agree" : tos_uuid,
                "tos_agree_timestamp" : datetime.utcnow()
            }
        })
        return dumps({
            "success" : True,
            "message" : f"🤝 Agreement {tos_uuid} accepted by {user_id}"
        })
