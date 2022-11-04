# cancel.py

from flask import Blueprint, render_template, current_app, _request_ctx_stack, request
from datetime import datetime, timedelta
from bson.json_util import dumps
from loguru import logger
import traceback
from ..utils import db, delete_piece
from ..utils.auth_utils import requires_auth, requires_vetting

blueprint = Blueprint('cancel', __name__)

@blueprint.route("/v3/cancel", methods=["POST"])
@requires_auth
@requires_vetting
def v3_cancel():
    current_user = _request_ctx_stack.top.current_user
    discord_id = int(current_user["sub"].split("|")[2])
    job_uuid = request.json.get("uuid")
    with db.get_database() as client:
        job = client.database.queue.find_one({"uuid": job_uuid, "author" : discord_id})
        logger.info(job)
        if not job:
            logger.info(f"❌ Cancel Error: {job_uuid} not found for {discord_id}")
            return dumps({
                "message" : "Job could not be marked for cancel.",
                "success" : False
            })


    with db.get_database() as client:
        client.database.queue.delete_one({"uuid": job_uuid, "author" : discord_id})       

    return dumps({
        "message" : "Job cancelled.",
        "success" : True
    })