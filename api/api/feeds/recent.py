# recent.py

from flask import Blueprint, render_template, current_app, _request_ctx_stack
from datetime import datetime, timedelta
from bson.json_util import dumps
from loguru import logger
import traceback
from ..utils import db
from ..utils.auth_utils import supports_auth

blueprint = Blueprint('recent', __name__)
@blueprint.route("/v3/recent/<type>/<amount>", methods=["GET"], defaults={"page": 1})
@blueprint.route("/v3/recent/<type>/<amount>/<page>")
@supports_auth
def v3_recent(type, amount, page):
    user_info = _request_ctx_stack.top.user_info
    current_user = _request_ctx_stack.top.current_user
    if user_info:
        user_id = int(user_info["user_id"].split("|")[2])
    else:
        user_id = None
    # fix
    if current_user:
        user_id = int(current_user["sub"].split("|")[2])

    q = {
        "nsfw": {"$nin": [True]},
        "hide": {"$nin": [True]},
        "thumbnails" : {"$exists" : True},
        "origin": "web",
        "status" : "complete"
    }
    if type == "disco":
        q["algo"] = "disco"
    
    if type == "stable":
        q["algo"] = "stable"
        q["origin"] = "web"

    if type == "dream":
        q["algo"] = "stable"
        q["origin"] = "dream"

    if type == "hallucination":
        q["algo"] = "stable"
        q["origin"] = "hallucination"

    if type == "general":
        q["algo"] = "disco"
        q["diffusion_model"] = {"$in" : ["512x512_diffusion_uncond_finetune_008100","256x256_diffusion_uncond"]}

    if type == "portraits":
        q["algo"] = "disco"
        q["diffusion_model"] = {"$in" : [
            "portrait_generator_v001_ema_0.9999_1MM",
            "portrait_generator_v1.5_ema_0.9999_165000",
            "portrait_generator_v003",
            "portrait_generator_v004",
            "512x512_diffusion_uncond_entmike_ffhq_025000",
            "512x512_diffusion_uncond_entmike_ffhq_145000",
            "512x512_diffusion_uncond_entmike_ffhq_260000"
            ]}

    if type == "isometric":
        q["algo"] = "disco"
        q["diffusion_model"] = {"$in" : ["IsometricDiffusionRevrart512px"]}

    if type == "pixel-art":
        q["algo"] = "disco"
        q["diffusion_model"] = {"$in" : ["pixel_art_diffusion_hard_256","pixel_art_diffusion_soft_256","pixelartdiffusion4k"]}

    if type == "paint-pour":
        q["diffusion_model"] = {"$in" : ["PaintPourDiffusion_v1.0","PaintPourDiffusion_v1.1","PaintPourDiffusion_v1.2","PaintPourDiffusion_v1.3"]}

    operations = [
        {"$match": q},
        {"$sort": {"_id": 1}},
        {"$sort": {"timestamp_completed": -1}},
        {"$addFields":{
            "likes": "$pins"
        }},
        {"$lookup": {"from": "vw_users", "localField": "author", "foreignField": "user_id", "as": "userdets"}},
        {"$skip": (int(page) - 1) * int(amount)},
        {"$limit": int(amount)},
        {"$unwind": {
            "path": "$userdets",
            "preserveNullAndEmptyArrays" : True
        }},
        {"$addFields": {"userdets.user_str": {"$toString": "$userdets.user_id"}}},
    ]
    if user_id:
        operations.append({
        "$lookup" : {
            "from": "pins",
            "let": {
                "user": user_id,
                "uuid" : "$uuid"
            },
            "pipeline": [{
                "$match": {
                    "$and": [
                        {"$expr": {"$eq": ['$user_id', '$$user'] }},
                        {"$expr": {"$eq": ['$uuid', '$$uuid'] }},
                    ]
                }
            }],
            "as": "pinned"
        }})
        operations.append({
            "$unwind" : {
                "path": "$pinned",
                "includeArrayIndex": 'string',
                "preserveNullAndEmptyArrays": True
            }
        })

    with db.get_database() as client:
        r = list(client.database.pieces.aggregate(operations))
        
        # Strip private params out
        for piece in r:
            try:
                if piece["private"] and piece["author"] != user_id:
                    del piece["params"]
            except:
                pass
        
        return dumps(r)