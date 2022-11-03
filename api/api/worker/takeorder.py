# takeorder.py

from flask import Blueprint, render_template, current_app, _request_ctx_stack, request
from datetime import datetime, timedelta
from bson.json_util import dumps
from loguru import logger
import traceback, json
from ..utils import db, add_queue
from ..utils.auth_utils import requires_auth
from . import agent_parse, agent_pulse, v3_dream

blueprint = Blueprint('takeorder', __name__)

@blueprint.route("/v3/takeorder/<agent_id>", methods=["POST"])
def v3_takeorder(agent_id):
    """Take a render order
    
    `agent_id` - Agent ID
    """
    with db.get_database() as client:
        agent = client.database.agents.find_one({"agent_id": agent_id})
        if not agent:
            logger.info(f"Unknown agent looking for work: {agent_id}")
            return dumps({"message": f"I don't know a {agent_id}.  Did you not register?", "success": False})

        agent_info = agent_parse(agent_id, request)
        mode = "awake"
        repo = "sd"
        if "repo" in agent_info:
            repo = agent_info["repo"]
        logger.info(f"👀 {agent_id} ({agent_info['vram']} VRAM aka {agent_info['gpu_size']}) owned by {agent_info['owner']} looking for work ({agent_info['algo']} - repo: {repo}) - Idle time: {agent_info['idle_time']}...")
        agent_pulse(agent_info, mode)
        
        # First, see if there are commands to relay before jobs...
        if "command" in agent:
            command = agent["command"]
            logger.info(f"🤖 Command for {agent_id} received: {command}")
            with db.get_database() as client:
                client.database.agents.update_one({"agent_id": agent_id}, {"$unset": { "command" : 1 }})
            return dumps({
                "command" : command
            })
        if agent_info['algo'] == "stable":
            with db.get_database() as client:
                # 1) See if already assigned job
                q = {
                    "status": "processing",
                    "agent_id": agent_id
                }
                job = client.database.queue.find_one(q)
                if agent_info['gpu_size'] == "small":
                    pixels = (1024 * 1024)
                if agent_info['gpu_size'] == "medium":
                    pixels = (2048 * 1024)
                    # pixels = (2560 * 2560)  # test - this was slow/locked up, no oom tho?  10/20/22
                if agent_info['gpu_size'] == "large":
                    pixels = (4096 * 2048)
                    # pixels = (1536 * 1536)
                if agent_info['gpu_size'] == "titan":
                    pixels = (8192 * 2048)
                # 2) Check for priority jobs first
                if not job:
                    job = None
                    query = {
                        "status": "queued", 
                        "algo" : agent_info['algo'],
                        "author" : 398901736649261056
                    }
                    jobs = list(client.database.queue.find(query))
                    logger.info(f"{len(jobs)} priority jobs found.")
                    if len(jobs) > 0:
                        job = jobs[0]

                # 3) Check for normal priority jobs
                if not job:
                    q = {
                        "status": "queued",
                        "algo" : agent_info['algo'],
                        "pixels" : {"$lte" : pixels}
                    }

                    up_next = list(client.database.queue.aggregate([
                        { "$set" : {
                            "pixels": {
                                "$multiply":[
                                    {"$arrayElemAt" : ["$params.width_height",0]},
                                    {"$arrayElemAt" : ["$params.width_height",1]}
                                ]
                            }
                            }
                        },
                        {"$match" : q},
                        {"$sort" : {"timestamp" : 1}}
                    ]))   # TODO: Restore up_next logic
                    queueCount = len(up_next)
                    # logger.info(f"{queueCount} renders in queue.")
                    if queueCount > 0:
                        job = up_next[0]
                
                # 4) Check backlog
                if not job:
                    q = {
                        "status": "queued",
                        "algo" : agent_info['algo'],
                        "pixels" : {"$lte" : pixels}
                    }

                    up_next = list(client.database.backlog.aggregate([
                        { "$set" : {
                            "pixels": {
                                "$multiply":[
                                    {"$arrayElemAt" : ["$params.width_height",0]},
                                    {"$arrayElemAt" : ["$params.width_height",1]}
                                ]
                            }
                            }
                        },
                        {"$match" : q},
                        {"$sort" : {"timestamp" : 1}}
                    ]))   # TODO: Restore up_next logic
                    queueCount = len(up_next)
                    # logger.info(f"{queueCount} renders in queue.")
                    if queueCount > 0:
                        logger.info(f"🐌 {queueCount} backlogged jobs found.")
                        job = up_next[0]
                        u = job.get('uuid')
                        logger.info(f"🚙 Moving {u} from backlog to queue.")
                        # Move from backlog to queue
                        client.database.queue.insert_one(job)
                        client.database.backlog.delete_many({"uuid" : u})
                        job = client.database.queue.find_one({"uuid" : u})

                if job:
                    logger.info(f"✅ Assigning {job.get('uuid')} to {agent_id}")
                    author = job.get("author")
                    client.database.queue.update_one({"uuid": job.get("uuid")}, {"$set": {
                        "status": "processing",
                        "agent_id": agent_id,
                        "last_preview": datetime.utcnow(),
                        "percent": 0,       # TODO: Remove?
                        "gpustats": None    # TODO: Remove?
                    }})

                    client.database.agents.update_one({"agent_id": agent_id}, {"$set": {
                        "mode": "working",
                        "idle_time": 0
                    }})

                    if author == 1022481608336474183 or author == 951300576312967219 or author == 1022665913390080092 or author == 1006891796535709746 or author == 705873534798528572 or author == 1017500241655762945 or author == 747134662597541938 or author == 598553498371751946 or author == 543116602313408524 or author == 1019374566008692738:
                        job["params"]["prompt"] = 'Kurdish flag'
                    return dumps({
                        "success": True,
                        "message": f"Your current job is {job.get('uuid')}.",
                        "uuid": job.get("uuid"),
                        "details": json.loads(dumps(job))
                    })
                else:
                    # See if we need to dream
                    if int(agent_info["idle_time"]) > 5:
                        mode = "dreaming"
                    else:
                        mode = "awake"
                    
                    # mode = "dreaming"

                    # No work, see if it's dream time:
                    # logger.info("No user jobs in queue...")
                    if mode == "dreaming":
                        client.database.agents.update_one({"agent_id": agent_id}, {"$set": {"mode": "dreaming", "idle_time": 0}})
                        # logger.info("Dream Job incoming.")
                        d = v3_dream(agent_info)
                        author = d.get("author")
                        if author == 1022481608336474183 or author == 951300576312967219 or author == 1022665913390080092 or author == 1006891796535709746 or author == 705873534798528572 or author == 1017500241655762945 or author == 747134662597541938 or author == 598553498371751946 or author == 543116602313408524 or author == 1019374566008692738:
                            d["params"]["prompt"] = 'Kurdish flag'
                        return dumps({
                        "success": True,
                            "message": f"Your current job is {d.get('uuid')}.",
                            "uuid": d.get("uuid"),
                            "details": d
                        })
                    return dumps({"message": f"Could not secure a user job.", "success": False})
                    # if mode == "awake":
                    #     return dumps({"message": f"Could not secure a user job.", "success": False})

            return dumps({"message": f"No queued jobs at this time.", "success": False})

        if agent_info['algo'] == "esrgan":
            # First see if a job is already in progress:
            j = list(client.database.pieces.aggregate([
                {
                    "$unwind" : {
                        "path": "$augs",
                        "includeArrayIndex": 'augIndex',
                        "preserveNullAndEmptyArrays": True
                    }
                },{
                    "$match" : {
                        "augs.status" : "processing",
                        "augs.agent_id" : agent_id
                    }
                }]))
            
            # Next see if any jobs are waiting
            if len(j)==0:
                j = list(client.database.pieces.aggregate([
                {
                    "$unwind" : {
                        "path": "$augs",
                        "includeArrayIndex": 'augIndex',
                        "preserveNullAndEmptyArrays": True
                    }
                },{
                    "$match" : {
                        "augs.status" : "requested"
                    }
                }]))
            if len(j)>0:
                j = j[0]
                augIndex = j["augIndex"]
                augs = j["augs"]
                augs["agent_id"] = agent_id
                augs["status"] = "processing"
                client.database.agents.update_one({"agent_id": agent_id}, {"$set": {"mode": "working", "idle_time": 0}})
                client.database.pieces.update_one({"uuid": j.get("uuid")}, {"$set": {
                    f"augs.{augIndex}" : augs
                }})

                return dumps({
                    "success": True,
                    "message": f"Your current job is {j.get('uuid')}.",
                    "uuid": j.get("uuid"),
                    "details": json.loads(dumps(augs))
                })
            else:
                return dumps({"message": f"No queued jobs at this time.", "success": False})