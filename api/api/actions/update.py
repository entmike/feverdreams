# update.py

from types import SimpleNamespace
from flask import Blueprint, render_template, current_app, _request_ctx_stack, request
from datetime import datetime, timedelta
from bson.json_util import dumps
from loguru import logger
import traceback, json, hashlib, random
from ..utils import db, add_queue
from ..utils.auth_utils import requires_auth, requires_vetting

blueprint = Blueprint('update', __name__)

@blueprint.route("/v3/review/update", methods=["POST"])
@requires_auth
@requires_vetting
def review_update():
    user_info = _request_ctx_stack.top.user_info
    # user_id = int(user_info["user_id"].split("|")[2])
    current_user = _request_ctx_stack.top.current_user
    user_id = int(current_user["sub"].split("|")[2])
    timestamp = datetime.utcnow()
    logger.info(request.json)
    job = request.json.get("review")
    with db.get_database() as client:
        j = client.database.reviews.find_one({"uuid" : job["uuid"], "author" : user_id})
        if not j:
            return dumps({
                "success" : False,
                "message" : f"You cannot update {j['uuid']}."
            })
        else:
            logger.info(f"Updating review {job['uuid']} by {str(user_id)}...")
            with db.get_database() as client:
                nsfw = False
                private = False
                
                if "nsfw" in job:
                    nsfw = job["nsfw"]

                if "private" in job:
                    private = job["private"]

                updateParams = {
                    "private" : private,
                    "nsfw" : nsfw,
                }

                client.database.reviews.update_one({"uuid": job["uuid"], "author" : user_id}, {"$set": updateParams})
            
            return dumps({
                "success" : True,
                "message" : f"{job['uuid']} successfully updated."
            })
