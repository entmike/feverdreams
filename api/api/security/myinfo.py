# myinfo.py

from flask import Blueprint, render_template, current_app, _request_ctx_stack
from datetime import datetime, timedelta
from bson.json_util import dumps
from loguru import logger
import traceback
from ..utils import db
from ..utils.auth_utils import requires_auth

blueprint = Blueprint('myinfo', __name__)

@blueprint.route("/v3/myinfo", methods=["GET"])
@requires_auth
def fn_myinfo():
    user_info = _request_ctx_stack.top.user_info
    user_pass = _request_ctx_stack.top.user_pass
    current_user = _request_ctx_stack.top.current_user
    user_id = int(current_user["sub"].split("|")[2])
    try:
        with db.get_database() as client:
            r = list(client.database.reviews.aggregate([
                {"$match" : {"author":user_id}}
            ]))
            q = list(client.database.queue.aggregate([
                {"$match" : {"author":user_id}}
            ]))
            b = list(client.database.backlog.aggregate([
                {"$match" : {"author":user_id}}
            ]))
            tos = list(client.database.tos.aggregate([
                {"$sort" : {"timestamp" : -1}},
                {"$limit" : 1}
            ]))
            u = client.database.users.find_one({"user_id" : user_id})
            invites = 0
            if u:
                invites = u.get("invites")
                if not invites:
                    invites = 0

            tosAgree = list(client.database.users.aggregate([
                {"$match" : {"user_id":user_id, "tos_agree" : tos[0].get("uuid")}}
            ]))
            agree = False
            if len(tosAgree) > 0:
                agree = True
            return dumps({
                "success" : True,
                "reviews" : len(r),
                "queue" : len(q),
                "backlog" : len(b),
                "tos" : tos[0],
                "invites" : invites,
                "tosAgree" : agree,
                "vetted" : user_pass
            })
    except:
        tb = traceback.format_exc()
        logger.error(tb)
        return dumps({
            "success" : False,
            "message" : "An error occured while getting your info.",
            "traceback" : tb
        })