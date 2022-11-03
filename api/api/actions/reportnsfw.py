# reportnsfw.py

from flask import Blueprint, render_template, current_app, _request_ctx_stack, request
from datetime import datetime, timedelta
from bson.json_util import dumps
from loguru import logger
import traceback
from ..utils import db
from ..utils.auth_utils import requires_auth

blueprint = Blueprint('reportnsfw', __name__)

@blueprint.route("/reportnsfw", methods=["POST"])
@requires_auth
def reportnsfw():
    current_user = _request_ctx_stack.top.current_user
    discord_id = int(current_user["sub"].split("|")[2])
    job = request.json.get("job")
    nsfw_count = 0
    with db.get_database() as client:
        j = client.database.pieces.find_one({"uuid" : job["uuid"]})
        if not j:
            return dumps({
                "success" : False,
                "message" : f"Cannot report piece: {j['uuid']}."
            })
        else:
            try:
                n = client.database.nsfw_reports.find_one({"uuid" : job["uuid"], "reported_by" : discord_id})
            except:
                n = None
            
            if not n:
                client.database.nsfw_reports.insert_one({
                    "uuid" : job["uuid"],
                    "timestamp" : datetime.utcnow(),
                    "reported_by" : discord_id,
                    "new" : True
                })
                return dumps({
                    "success" : True,
                    "message" : f"Piece {j['uuid']} reported as NSFW.  Thank you!"
                })
            else:
                return dumps({
                "success" : True,
                "message" : f"You already reported this."
            })