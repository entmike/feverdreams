# register.py

from flask import Blueprint, render_template, current_app, _request_ctx_stack, request
from datetime import datetime, timedelta
from bson.json_util import dumps
from loguru import logger
from werkzeug.utils import secure_filename
import traceback, json, os, hashlib
from ..utils import db, add_queue
from ..utils.auth_utils import requires_auth
from . import agent_parse, agent_pulse, v3_dream, allowed_file, v3_postProcess

blueprint = Blueprint('register', __name__)

@blueprint.route("/register/<agent_id>")
def register(agent_id):
    status = ""
    with db.get_database() as client:
        agentCollection = client.database.get_collection("agents")
        if agentCollection.count_documents({"agent_id": agent_id}) == 0:
            found = False
        else:
            found = True

        if not found:
            token = hashlib.sha256(f"{agent_id}{current_app.config['BOT_SALT']}".encode("utf-8")).hexdigest()
            agentCollection.insert_one({"agent_id": agent_id, "last_seen": datetime.utcnow()})
            status = f"✅ Registered!  Your API token is '{token}'.  Save this, you won't see it again."
            # log(f"A new agent has joined! 😍 Thank you, {agent_id}!", title="🆕 New Agent")
            success = True
        else:
            status = f"😓 Sorry, someone already registered an agent by that name.  Try another one!"
            success = False
    return dumps({"message": status, "success": success})