# landingpage.py

from flask import Blueprint, render_template, current_app
from datetime import datetime, timedelta
from json import dumps
from ..utils import db

landingpage = Blueprint('landingpage', __name__)

@landingpage.route("/v3/landingstats")
def v3_landingstats():
    with db.get_database() as client:
        since = datetime.utcnow() - timedelta(minutes=60)
        userCount = client.database.users.count_documents({})
        completedCount = client.database.pieces.count_documents({})
        deletedCount = client.database.deleted_pieces.count_documents({})
        reviewCount = client.database.reviews.count_documents({})
        agentCount = client.database.agents.count_documents({"last_seen": {"$gt": since}})
        return dumps(
            {
                "completedCount": (completedCount + deletedCount + reviewCount),
                "userCount": userCount,
                "agentCount": agentCount,
            }
        )

