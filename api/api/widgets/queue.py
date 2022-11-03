# queue.py

import uuid
from flask import Blueprint
from datetime import datetime, timedelta
from bson.json_util import dumps
from loguru import logger
import traceback
from ..utils import db, v3_queue

blueprint = Blueprint('queue', __name__)

@blueprint.route("/v3/public_queue/", methods=["GET"], defaults={"status": "all"})
@blueprint.route("/v3/public_queue/<status>/")
def v3_public_queue(status):
    queue = v3_queue(status)
    
    # Strip private params out
    for item in queue:
        item["width_height"] = item["params"]["width_height"]
        if "private" in item:
            try:
                if item["private"]:
                    del item["params"]
            except:
                pass
        

    return dumps(queue)