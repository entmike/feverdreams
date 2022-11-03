# tags.py

from flask import Blueprint, render_template, current_app, _request_ctx_stack
from datetime import datetime, timedelta
from bson.json_util import dumps
from loguru import logger
import traceback
from ..utils import db
from ..utils.auth_utils import supports_auth

blueprint = Blueprint('tags', __name__)
@blueprint.route("/v3/tags", methods=["GET"])
@supports_auth
def v3_tags():
    current_user = _request_ctx_stack.top.current_user
    if current_user:
        user_id = int(current_user["sub"].split("|")[2])
    else:
        user_id = None
    
    q = {}
    
    operations = [
        {"$match": q},
        {"$sort": {"tag": 1}}
    ]
    with db.get_database() as client:
        r = list(client.database.tags.aggregate(operations))
        return dumps(r)