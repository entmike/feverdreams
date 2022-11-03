# create.py

from types import SimpleNamespace
from flask import Blueprint, render_template, current_app, _request_ctx_stack, request
from datetime import datetime, timedelta
from bson.json_util import dumps
from loguru import logger
import traceback, json, hashlib, random
from ..utils import db, add_queue
from ..utils.auth_utils import requires_auth, requires_vetting

blueprint = Blueprint('create', __name__)

@blueprint.route("/v3/create/edit", methods=["POST"], defaults={"mode" : "edit"})
@blueprint.route("/v3/create/update", methods=["POST"], defaults={"mode" : "update"})
@blueprint.route("/v3/create/mutate", methods=["POST"], defaults={"mode" : "mutate"})
@requires_auth
@requires_vetting
def create(mode):
    user_info = _request_ctx_stack.top.user_info
    # user_id = int(user_info["user_id"].split("|")[2])
    current_user = _request_ctx_stack.top.current_user
    user_id = int(current_user["sub"].split("|")[2])
    timestamp = datetime.utcnow()
    # logger.info(f"📷 Incoming job request ({mode}) from {user_id} ({user_info['name']})...")
    job = request.json.get("job")
    
    # NEW/EDIT
    if mode == "mutate" or mode == "edit":
        jobparams = job["params"]
        
        repo = "sd"
        if "repo" in job:
            repo = job["repo"]

        # DEFAULTS (A1111)
        args = {
            "enable_hr" : False,
            "tiling" : False,
            "restore_faces" : False,
            "firstphase_width" : 0,
            "firstphase_height" : 0,
            "denoising_strength" : 0.75,
            "prompt" : "A lonely robot",
            "negative_prompt" : "",
            "seed" : 0,
            "sampler_index" : 0,
            "n_iter" : 1,
            "steps" : 20,
            "scale" : 7.0,
            "img2img" : False,
            "img2img_denoising_strength" : 0.75,
            "img2img_source_uuid" : "UNKNOWN"
        }

        if job["algo"] == "stable":
            # weights_hash = "fe4efff1e174c627256e44ec2991ba279b3816e364b49f9be2abc0b3ff3f8556" # 1.4
            weights_hash = "cc6cb27103417325ff94f52b7a5d2dde45a7515b25c255d8e396c90014281516" # 1.5
        else:
            weights_hash = "N/A"

        for param in ["prompt","negative_prompt","scale","steps","seed","denoising_strength","restore_faces","tiling","enable_hr",
            "firstphase_width","firstphase_height","img2img","img2img_denoising_strength","img2img_source_uuid"]:
            if param in jobparams:
                args[param] = jobparams[param]

        seed = int(args["seed"])
        prompt = args["prompt"]
        if args["img2img_denoising_strength"] is None:
            args["img2img_denoising_strength"] = 0.75
        try:
            sampler = jobparams["sampler"]
        except:
            sampler = "k_lms"
        
        review = True
        
        batchparams = {
            "repo" : repo,
            "author" : user_id,
            "weights" : weights_hash,     #1.4
            "n_samples" : 1,
            "prompt": args["prompt"],
            "negative_prompt": args["negative_prompt"],
            "restore_faces": args["restore_faces"],
            "enable_hr": args["enable_hr"],
            "denoising_strength": args["denoising_strength"],
            "steps": args["steps"],
            "scale": args["scale"],
            "eta": jobparams["eta"],
            "width_height": jobparams["width_height"],
            "sampler": sampler,
            "img2img" : args["img2img"],
            "img2img_denoising_strength" : args["img2img_denoising_strength"],
            "img2img_source_uuid" : args["img2img_source_uuid"]
        }
        ns_batch_params = SimpleNamespace(**batchparams)
        bp = json.dumps(ns_batch_params.__dict__, indent = 4)

        batch_hash = str(hashlib.sha256(bp.encode('utf-8')).hexdigest())
        prompt_hash = str(hashlib.sha256(args["prompt"].encode('utf-8')).hexdigest())

        try:
            batch_size = int(job["batch_size"])
        except:
            batch_size = 1
        if seed == -1:
            seed = random.randint(0, 2**32)
        results = []
        for i in range(batch_size):
            new_seed = seed+i
            # logger.info(f"{i+1} of {batch_size} - Seed: {seed+i}")
            params = {
                "repo" : repo,
                "weights" : weights_hash,     #1.4
                "n_samples" : 1,
                "prompt": args["prompt"],
                "negative_prompt": args["negative_prompt"],
                "restore_faces": args["restore_faces"],
                "enable_hr": args["enable_hr"],
                "denoising_strength": args["denoising_strength"],
                "seed": new_seed,
                "steps": args["steps"],
                "scale": args["scale"],
                "eta": jobparams["eta"],
                "width_height": jobparams["width_height"],
                "sampler": sampler,
                "img2img" : args["img2img"],
                "img2img_denoising_strength" : args["img2img_denoising_strength"],
                "img2img_source_uuid" : args["img2img_source_uuid"]
            }

            ns_params = SimpleNamespace(**params)
            p = json.dumps(ns_params.__dict__, indent = 4)
            param_hash = str(hashlib.sha256(p.encode('utf-8')).hexdigest())

            newrecord = {
                "weights" : weights_hash,
                "batch_hash" : batch_hash,
                "hide": False,
                "review": review,
                "uuid": param_hash,
                "preferred_image" : param_hash,
                "algo" : "stable",
                "repo" : "a1111",
                "nsfw": job["nsfw"],
                "private": job["private"],
                "author": user_id,
                "status": "queued",
                "timestamp": timestamp,
                "origin": "web",
                "n_samples" : 1,
                "prompt_hash" : prompt_hash,
                # "gpu_preference": job["gpu_preference"],
                "width_height": jobparams["width_height"],
                "params" : ns_params.__dict__
            }
            
            with db.get_database() as client:
                j = client.database.vw_all.find_one({"uuid" : param_hash})
                if j:
                    logger.warning(f"⚠️ Hash {param_hash} already exists.")
                    results.append({
                        "success" : False,
                        "uuid" : param_hash,
                        "message" : f"Render {param_hash} already exists."
                    })
                else:
                    # logger.info(f"Adding job {param_hash} to queue.")
                    if mode == "mutate":
                        add_queue(newrecord)
                        results.append({
                            "success" : True,
                            "uuid" : param_hash,
                            "message" : f"✅ Render {param_hash} submitted successfully."
                        })
                    if mode == "edit":
                        old_hash = job["uuid"]
                        client.database.queue.update_one({"uuid":old_hash},{
                            "$set" : newrecord
                        })
                        results.append({
                            "success" : True,
                            "uuid" : param_hash,
                            "message" : f"✅ Render {param_hash} editted successfully."
                        })
        return dumps({"success" : True, "results" : results})
   
    # UPDATE
    if mode == "update":
        with db.get_database() as client:
            j = client.database.vw_all.find_one({"uuid" : job["uuid"], "author" : user_id})
            if not j:
                return dumps({
                    "success" : False,
                    "message" : f"You cannot update {j['uuid']}."
                })
            else:
                logger.info(f"Updating job {job['uuid']} by {str(user_id)}...")
                with db.get_database() as client:
                    if "preferredImage" in job:
                        preferred_image = job["preferredImage"]
                    else:
                        preferred_image = job["uuid"]
                    
                    if "nsfw" in job:
                        nsfw = job["nsfw"]
                    else:
                        nsfw = False

                    if "hide" in job:
                        hide = job["hide"]
                    else:
                        hide = False

                    if "private" in job:
                        private = job["private"]
                    else:
                        private = False

                    updateParams = {
                        "private" : private,
                        "nsfw" : nsfw,
                        "hide" : hide,
                        "preferredImage" : preferred_image
                    }
                    client.database.get_collection(j["source"]).update_one({"uuid": job["uuid"], "author" : user_id}, {"$set": updateParams})
                return dumps({
                    "success" : True,
                    "message" : f"{job['uuid']} successfully updated."
                })
    

    return dumps({"success" : False, "results" : "Unknown instruction"})