# reject.py

from flask import Blueprint, render_template, current_app, _request_ctx_stack, request
from datetime import datetime, timedelta
from bson.json_util import dumps
from loguru import logger
from werkzeug.utils import secure_filename
import traceback, json, os
from ..utils import db, add_queue
from ..utils.auth_utils import requires_auth
from . import pulse

blueprint = Blueprint('reject', __name__)

@blueprint.route("/v3/reject/<agent_id>/<job_uuid>", methods=["POST"])
def v3_reject(agent_id, job_uuid):
    pulse(agent_id=agent_id)
    logger.error(f"❌ Rejecting {job_uuid} - Details in traceback in DB.")
    tb = request.form.get("traceback")
    log = request.form.get("log")
    # logger.info(log)
    # logger.info(tb)
    if request.method == "POST":
        with db.get_database() as client:
            queueCollection = client.database.queue
            results = queueCollection.update_one({"agent_id": agent_id, "uuid": job_uuid}, {"$set": {"status": "failed", "filename": None, "log": log, "traceback": tb}})
            count = results.modified_count
            # if it's a dream delete it.
            results = queueCollection.delete_many({"agent_id": agent_id, "uuid": job_uuid, "render_type" : "dream"})
        if count == 0:
            return f"cannot find that job."
        else:
            return f"job rejected, {agent_id}."