# rolldice.py

from types import SimpleNamespace
from flask import Blueprint, render_template, current_app, _request_ctx_stack, request
from datetime import datetime, timedelta
from bson.json_util import dumps
from loguru import logger
import traceback, json, hashlib, random
from ..utils import db, add_queue
from ..utils.auth_utils import requires_auth, requires_vetting

blueprint = Blueprint('rolldice', __name__)

@blueprint.route("/v3/rolldice", methods=["POST"])
@requires_auth
@requires_vetting
def rolldice():
    user_info = _request_ctx_stack.top.user_info
    # user_id = int(user_info["user_id"].split("|")[2])
    current_user = _request_ctx_stack.top.current_user
    user_id = int(current_user["sub"].split("|")[2])
    timestamp = datetime.utcnow()
    j = request.json

    with db.get_database() as client:
        piece = client.database.reviews.find_one({
            "uuid" : j["uuid"],
            "author" : user_id
        },{"_id":0})
        if piece:
            seed = random.randint(0, 2**32)
            for i in range(j['amount']):
                logger.info(f"🎲 {i}")
                np = piece.get("params")
                np['seed']=seed + i
                np['repo']="a1111"
                ns_params = SimpleNamespace(**np)
                p = json.dumps(ns_params.__dict__, indent = 4)
                param_hash = str(hashlib.sha256(p.encode('utf-8')).hexdigest())
                # weights_hash = "fe4efff1e174c627256e44ec2991ba279b3816e364b49f9be2abc0b3ff3f8556" # 1.4
                weights_hash = "cc6cb27103417325ff94f52b7a5d2dde45a7515b25c255d8e396c90014281516" # 1.5
                newrecord = {
                    "weights" : weights_hash,
                    "batch_hash" : piece["batch_hash"],
                    "hide": False,
                    "review": True,
                    "uuid": param_hash,
                    "preferred_image" : param_hash,
                    "algo" : "stable",
                    "repo" : "a1111",
                    "nsfw": piece["nsfw"],
                    "private": piece["private"],
                    "author": user_id,
                    "status": "queued",
                    "timestamp": datetime.utcnow(),
                    "origin": "web",
                    "n_samples" : 1,
                    "prompt_hash" : piece["prompt_hash"],
                    "width_height": piece["width_height"],
                    "params" : ns_params.__dict__
                }
                add_queue(newrecord)
            return dumps({"success" : True, "message" : "Dice rolled"})
    return dumps({"success" : False, "message" : "Piece not in DB"})