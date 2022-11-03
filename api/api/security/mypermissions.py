# mypermissions.py

from flask import Blueprint, render_template, current_app, _request_ctx_stack
from datetime import datetime, timedelta
from bson.json_util import dumps
from loguru import logger
import traceback
from ..utils import db
from ..utils.auth_utils import requires_auth, my_permissions

blueprint = Blueprint('mypermissions', __name__)

@blueprint.route("/mypermissions", methods=["GET"])
@requires_auth
def mypermissions():
    return dumps(my_permissions())