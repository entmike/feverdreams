# myjobs.py

from flask import Blueprint, render_template, current_app, _request_ctx_stack, request
from datetime import datetime, timedelta
from bson.json_util import dumps
from loguru import logger
import traceback
from ..utils import db
from ..utils.auth_utils import requires_auth

blueprint = Blueprint('myjobs', __name__)

@blueprint.route("/v3/myjobs", methods=["GET"], defaults={"status": all, "page": 1})
@blueprint.route("/v3/myjobs/<status>", methods=["GET"], defaults={"status": all, "page": 1})
@blueprint.route("/v3/myjobs/<status>/<page>", methods=["GET"])
@requires_auth
def v3_myjobs(status, page):
    current_user = _request_ctx_stack.top.current_user
    user_info = _request_ctx_stack.top.user_info
    discord_id = int(current_user["sub"].split("|")[2])
    # status = "all"
    with db.get_database() as client:
        q = {"author" : {"$in": [discord_id, str(discord_id)]}}
        if status == "failed":
            q["status"]={"$in":["rejected","failed"]}
        if status == "queued":
            q["status"]={"$in":["queued"]}
            
        amount = 25
        with db.get_database() as client:
            jobs = client.database.vw_all.aggregate(
            [
                {"$match": q},
                {"$sort": {"timestamp": -1}},
                {"$skip": (int(page) - 1) * int(amount)},
                {"$limit": int(amount)}
            ])
        return dumps(jobs)