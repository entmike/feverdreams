# gpustats.py

import uuid
from flask import Blueprint
from datetime import datetime, timedelta
from bson.json_util import dumps
from loguru import logger
import traceback
from ..utils import db

blueprint = Blueprint('gpustats', __name__)

@blueprint.route("/agentstats")
def agent():
    with db.get_database() as client:
        since = datetime.utcnow() - timedelta(minutes=60)
        agents = client.database.agents.find({"last_seen": {"$gt": since}}).sort("last_seen", -1)
        return dumps(agents)

@blueprint.route("/agent/<agent_id>")
def agentstats(agent_id):
    with db.get_database() as client:
        agent = client.database.get_collection("agents").find_one({"agent_id": agent_id})
        return dumps(agent)

@blueprint.route("/web/agentjobs/<agent>", methods=["GET"], defaults={"page": 1})
@blueprint.route("/web/agentjobs/<agent>/<page>", methods=["GET"])
def web_agentjobs(agent, page):
    with db.get_database() as client:
        q = {"agent_id" : agent}
        amount = 25
        jobs = client.database.queue.aggregate(
            [
                {"$unionWith": { "coll": "pieces", "pipeline": [ { "$project": { "_id": 0 } } ]} },
                {"$match": q},
                {"$sort": {"timestamp": -1}},
                {"$skip": (int(page) - 1) * int(amount)},
                {"$limit": int(amount)}
            ])
        return dumps(jobs)