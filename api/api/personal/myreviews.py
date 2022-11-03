# myreviews.py

from flask import Blueprint, render_template, current_app, _request_ctx_stack, request
from datetime import datetime, timedelta
from bson.json_util import dumps
from loguru import logger
import traceback
from ..utils import db
from ..utils.auth_utils import requires_auth

blueprint = Blueprint('myreviews', __name__)

@blueprint.route("/v3/myreviews/<amount>", methods=["GET"], defaults={"page": 1})
@blueprint.route("/v3/myreviews/<amount>/<page>")
@requires_auth
def v3_myreviews(amount, page):
    user_info = _request_ctx_stack.top.user_info
    current_user = _request_ctx_stack.top.current_user
    user_id = int(current_user["sub"].split("|")[2])    
    try:
        q = {
            "author_id": int(user_id),
            "status" : "complete"
        }

        with db.get_database() as client:
            operations = [
                {
                    "$addFields": {"author_id": {"$toLong": "$author"}},
                },
                {"$match": q},
                {"$sort": {"time_completed": -1}},
                {"$skip": (int(page) - 1) * int(amount)},
                {"$limit": int(amount)},
                
            ]
            
            r = list(client.database.reviews.aggregate(operations))

            # Don't strip private params out
            
            return dumps(r)

    except:
        tb = traceback.format_exc()
        logger.error(tb)
        return dumps({
            "success" : False,
            "message" : "Delivery failed!",
            "traceback" : tb
        })
