# job.py

from flask import Blueprint, render_template, current_app, _request_ctx_stack, request
from datetime import datetime, timedelta
from bson.json_util import dumps
from loguru import logger
import traceback
from ..utils import db
from ..utils.auth_utils import supports_auth

blueprint = Blueprint('job', __name__)

@blueprint.route("/v3/meta/<job_uuid>", methods=["GET"], defaults={"mode" : "meta"})
@blueprint.route("/v3/job/<job_uuid>", methods=["GET"], defaults={"mode" : "view"})
@supports_auth
def v3_job(job_uuid, mode):
    auth = request.headers.get("Authorization", None)
    current_user = _request_ctx_stack.top.current_user
    # fix
    if current_user:
        user_id = int(current_user["sub"].split("|")[2])
    else:
        user_id = None
    
    if request.method == "GET":
        
        # logger.info(f"Accessing {job_uuid}...")
        with db.get_database() as client:
            queueCollection = client.database.all_pieces
            q = {
                "uuid" : job_uuid
            }
            if user_id is None:
                q["source"] = "pieces"
            else:
                q["$or"] = [
                    {"source" : {"$in":["pieces"]}},
                    {"author": user_id, "source" : {"$in":["personal_pieces"]}},
                ]
            operations = [
                {"$match": q},
                {"$addFields": {"author_bigint": {"$toLong": "$author"}}},
                {"$addFields": {"str_author": {"$toString": "$author"}}},
                {"$addFields":{
                    "likes": "$pins"
                }},
                {"$lookup": {"from": "vw_users", "localField": "author_bigint", "foreignField": "user_id", "as": "userdets"}},
                {"$unwind": {
                    "path": "$userdets",
                    "preserveNullAndEmptyArrays" : True
                }},
                {"$unwind": "$uuid"},
                {"$addFields": {
                    "userdets.user_str": {"$toString": "$userdets.user_id"},
                    "width_height": {"$toString": "$userdets.user_id"}
                    }
                },
            ]
            if user_id:
                operations.append(
                    # "$lookup": {"from": "pins", "localField": "uuid", "foreignField": "uuid", "as": "pinned"}
                    { "$lookup": {
                    "as": "pinned",
                    "from" : "pins",
                    "let" : { "uuid" : "$uuid" },
                    "pipeline": [
                        {
                            "$match": {
                                "$and": [
                                    {"$expr": {"$eq": ['$user_id', user_id] }},
                                    {"$expr": {"$eq": ['$uuid', '$$uuid'] }},
                                ]} 
                        },
                    ]}
                })
                operations.append({"$unwind": {
                    "path": "$pinned",
                    "preserveNullAndEmptyArrays" : True
                }})
            jobs = queueCollection.aggregate(operations)
            jobs = list(jobs)
            if len(jobs) == 0:
                return dumps(None)
            
            job = jobs[0]

            if mode == "view":
                try:
                    views = job["views"]
                except:
                    views = 0
                
                views += 1
                collection = job["source"]
                client.database.get_collection(collection).update_one({"uuid": job_uuid}, {"$set": {
                    "views": views
                }}, upsert=True)
                job["views"] = views
            
            # logger.info(job)
            # Strip private params out
            try:
                if job["private"] and job["author"] != user_id:
                    del job["params"]
            except:
                pass

            return dumps(job)