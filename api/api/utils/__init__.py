from . import db
from loguru import logger
from datetime import datetime, timedelta
from flask import current_app

def add_queue(newrecord):
    user_id = newrecord["author"]
    with db.get_database() as client:
        jobcount = len(list(client.database.queue.aggregate([
            {"$match" : {
                "author" : user_id,
                "status" : "queued"
            }}
        ])))
        
        if jobcount >= 50:
            destination = client.database.backlog
        else:
            destination = client.database.queue
        
        destination.insert_one(newrecord)

def v3_queue(status):
    logger.info(f"📃 Queue request for status {status}...")
    if status == "stalled":
        since = datetime.utcnow() - timedelta(minutes=current_app.config["BOT_STALL_TIMEOUT"])
        q = {"status": "processing", "timestamp": {"$lt": since}}
    else:
        q = {"status": {"$nin": ["archived", "rejected"]}}

    if status != "all" and status != "stalled" and status !="backlog":
        q["status"] = status
    
    with db.get_database() as client:
        query = {"$query": q, "$orderby": {"timestamp": -1}}
        logger.info(query)
        if status == "backlog":
            destination = client.database.backlog
        else:
            destination = client.database.queue
        queue = destination.aggregate(
            [
                {"$match": q},
                {"$lookup": {"from": "vw_users", "localField": "author", "foreignField": "user_id", "as": "userdets"}},
                {"$unwind": {
                    "path": "$userdets",
                    "preserveNullAndEmptyArrays" : True
                }},
                {"$unwind": "$uuid"},
                {"$addFields": {"userdets.user_str": {"$toString": "$userdets.user_id"}}},
                {"$addFields": {"processingTime": {"$subtract": [datetime.utcnow(),"$last_preview"]}}}, # milliseconds
            ]
        )
        return list(queue)

def delete_piece(author = None, uuid = None):
    with db.get_database() as client:
        piece = client.database.all_pieces.find_one({
            "uuid": uuid,
            "author": author
        })
        if piece:
            source = piece.get("source")
            del piece["source"]
            piece["timestamp_completed"] = datetime.utcnow()
            piece["deleted"] = True
            if source != "deleted_pieces":
                client.database.deleted_pieces.insert_one(piece)
                client.database.get_collection(source).delete_many({
                    "uuid": uuid,
                    "author": author
                })
                logger.info(f"🚫 Deleted {uuid} deleted moved from {source} to deleted_pieces.")
            else:
                logger.info(f"🚫 {uuid} is already in deleted_pieces.")
        else:
            logger.info(f"⚠️ Cannot find {uuid} from {author}.")

def undelete_piece(author = None, uuid = None):
    with db.get_database() as client:
        piece = client.database.all_pieces.find_one({
            "uuid": uuid,
            "author": author
        })
        if piece:
            source = piece.get("source")
            if source == "deleted_pieces":
                del piece["source"]
                piece["timestamp_completed"] = datetime.utcnow()
                piece["time_completed"] = datetime.utcnow()
                piece["deleted"] = False
                client.database.reviews.insert_one(piece)
                client.database.get_collection(source).delete_many({
                    "uuid": uuid,
                    "author": author
                })
                logger.info(f"👼 Piece {uuid} undeleted from {source} to reviews.")
            else:
                logger.info(f"⚠️ {uuid} is not in deleted_pieces.")
        else:
            logger.info(f"⚠️ Cannot find {uuid} from {author}.")