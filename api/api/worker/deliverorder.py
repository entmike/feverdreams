# deliverorder.py

from flask import Blueprint, render_template, current_app, _request_ctx_stack, request
from datetime import datetime, timedelta
from bson.json_util import dumps
from loguru import logger
from werkzeug.utils import secure_filename
import traceback, json, os
from ..utils import db, add_queue
from ..utils.auth_utils import requires_auth
from . import agent_parse, agent_pulse, v3_dream, allowed_file, v3_postProcess

blueprint = Blueprint('deliverorder', __name__)

@blueprint.route("/v3/deliverorder", methods=["POST"])
def v3_deliver_order():
    agent_id = request.form.get("agent_id")
    algo = request.form.get("algo")
    agent_version = request.form.get("agent_version")
    job_uuid = request.form.get("uuid")
    logger.info(f"🚚 {agent_id} ({algo}) delivering {job_uuid}")
    if request.form.get("duration"):
        duration = float(request.form.get("duration"))
    else:
        duration = 0.0

    # check if the post request has the file part
    if "file" not in request.files:
        return dumps({
            "success" : False,
            "message" : "No file received."
        })
    file = request.files["file"]
    if file.filename == "":
        return dumps({
            "success" : False,
            "message" : "No file received."
        })

    if file and allowed_file(file.filename):
        filename = secure_filename(f"{job_uuid}.png")
        filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)
    else:
        return dumps({
            "success" : False,
            "message" : "Unexpected file type."
        })
    
    # Since payload is saved, update job record.
    with db.get_database() as client:
        q = {"agent_id": agent_id, "uuid": job_uuid}
        piece = client.database.queue.find_one(q)
        if piece:
            review = piece.get("review")
            if not review:
                piece["timestamp_completed"] = datetime.utcnow()
                client.database.pieces.insert_one(piece)
                logger.info("✅ Delivery moved to pieces collection.")
            else:
                client.database.reviews.insert_one(piece)
                logger.info("✅ Delivery moved to reviews collection.")
            
            client.database.queue.delete_many(q)
            
        else:
            logger.info("❌ Unexpected delivery.  Ignoring.")
            import traceback
            tb = traceback.format_exc()
            logger.error(tb)
            return dumps({
                "success" : False,
                "message" : "Unexpected delivery."
            })
                
    try:
        v3_postProcess(job_uuid, algo, review)
        # Give agent a point
        with db.get_database() as client:
            results = client.database.agents.find_one({"agent_id": agent_id})
            score = results.get("score")
            if not score:
                score = 1
            else:
                score += 1
            results = client.database.agents.update_one({"agent_id": agent_id}, {"$set": {"score": score}})

        return dumps({
            "success" : True,
            "message" : "Delivery received!",
            "duration" : duration
        })
    except:
        import traceback
        tb = traceback.format_exc()
        logger.error(tb)
        return dumps({
            "success" : False,
            "message" : "Delivery failed!",
            "traceback" : tb
        })