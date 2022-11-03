# user.py

from flask import Blueprint, render_template, current_app, _request_ctx_stack
from datetime import datetime, timedelta
from bson.json_util import dumps
from loguru import logger
import traceback
from ..utils import db
from ..utils.auth_utils import supports_auth

blueprint = Blueprint('user', __name__)

@blueprint.route("/user/<user_id>", methods=["GET"])
def user(user_id):
    with db.get_database() as client:
        userCollection = client.database.vw_users
        user = userCollection.find_one({ "user_id_str" : user_id})
        if user:
            return dumps(user)
        else:
            return dumps({
                "user_id_str" : str(user_id),
                "user_name" : "Unknown User"
            })