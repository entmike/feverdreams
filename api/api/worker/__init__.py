import json, hashlib, random, os, boto3, botocore.exceptions, traceback
from datetime import datetime
from loguru import logger
from types import SimpleNamespace
from ..utils import db, add_queue, prompt_salad
from docarray import Document
from docarray import DocumentArray
from flask import current_app
from colorthief import ColorThief
from PIL import Image
from urllib.request import urlopen

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "log", "lz4"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def upload_file_s3(file_name, bucket, object_name=None, extra_args=None):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = os.path.basename(file_name)

    # Upload the file
    s3_client = boto3.client("s3",
        region_name = "us-east-1",
        aws_access_key_id = current_app.config['BOT_AWS_SERVER_PUBLIC_KEY'],
        aws_secret_access_key = current_app.config['BOT_AWS_SERVER_SECRET_KEY'])

    try:
        response = s3_client.upload_file(file_name, bucket, object_name, extra_args)
    except Exception as e:
        logger.error(e)
        return False
    return True

def s3_jpg(job_uuid, algo="disco"):
    try:
        if algo == "disco":
            try:
                url = f"{current_app.config['BOT_S3_WEB']}{job_uuid}0_0.png"
                img = Image.open(urlopen(url))
            except:
                url = f"{current_app.config['BOT_S3_WEB']}{job_uuid}.png"
                img = Image.open(urlopen(url))
        if algo == "stable":
            try:
                url = f"{current_app.config['BOT_S3_WEB']}{job_uuid}.png"
                img = Image.open(urlopen(url))
            except:
                url = f"{current_app.config['BOT_S3_WEB']}{job_uuid}.png"
                img = Image.open(urlopen(url))

        jpgfile = f"{job_uuid}.jpg"
        fn = os.path.join(current_app.config["UPLOAD_FOLDER"], jpgfile)
        logger.info(f"📷: {fn}")
        img.save(fn, "JPEG")
        upload_file_s3(fn, current_app.config['BOT_S3_BUCKET'], f"jpg/{jpgfile}", {"ContentType": "image/jpeg"})
        os.remove(fn)
    except Exception as e:
        tb = traceback.format_exc()
        logger.error(tb)
        return f"Could not locate {url}.  This might be because the render has not completed yet.  Or because the job failed.  Or check your job uuid.  Or a gremlin ate the image.  Probably the gremlin.\n{tb}"


def s3_thumbnail(job_uuid, size, algo="disco"):
    try:
        if algo == "disco":
            try:
                url = f"{current_app.config['BOT_S3_WEB']}{job_uuid}0_0.png"
                img = Image.open(urlopen(url))
            except:
                url = f"{current_app.config['BOT_S3_WEB']}{job_uuid}.png"
                img = Image.open(urlopen(url))
        if algo == "stable":
            try:
                url = f"{current_app.config['BOT_S3_WEB']}{job_uuid}.png"
                img = Image.open(urlopen(url))
            except:
                pass

        img.thumbnail((int(size), int(size)), Image.LANCZOS)
        thumbfile = f"thumb_{size}_{job_uuid}.jpg"
        fn = os.path.join(current_app.config["UPLOAD_FOLDER"], thumbfile)
        logger.info(f"👍: {fn}")
        img.save(fn, "JPEG")
        upload_file_s3(fn, current_app.config['BOT_S3_BUCKET'], f"thumbs/{size}/{job_uuid}.jpg", {"ContentType": "image/jpeg"})
        os.remove(fn)
    except Exception as e:
        tb = traceback.format_exc()
        logger.error(tb)
        return f"Could not locate {url}.  This might be because the render has not completed yet.  Or because the job failed.  Or check your job uuid.  Or a gremlin ate the image.  Probably the gremlin.\n{tb}"



def getOldestDream():
    with db.get_database() as client:
        # Get oldest dream
        dream = client.database.userdreams.find_one(
            {
                "$query": {
                    "version" : "2.0",
                    "count" : {"$lt" : 50}
                    # "author_id" : {"$ne": 823976252154314782}
                    # "$or" : [
                    #     {"count":{"$lt": 30}},
                    #     {"count":{"$exists": False}}
                    # ]
                },
                "$orderby": {"count": 1},
            }
        )
        if dream:
            return dream
        else:
            return None

def v3_dream(agent_info):
    type_seed = random.randint(0, 6)
    # weights_hash = "fe4efff1e174c627256e44ec2991ba279b3816e364b49f9be2abc0b3ff3f8556" # 1.4
    weights_hash = "cc6cb27103417325ff94f52b7a5d2dde45a7515b25c255d8e396c90014281516" # 1.5
    width_height = [512,512]
    if agent_info['gpu_size'] == "small":
        width_height = random.sample([[704,512], [512,704], [512,512]], 1)[0]
    if agent_info['gpu_size'] == "medium":
        width_height = random.sample([[704,512], [512,704], [512,512]], 1)[0]
    if agent_info['gpu_size'] == "large":
        width_height = random.sample([[1024,512], [512,1024], [1536,512], [512,1536]], 1)[0]
    
    # Ensure it's a unique job
    exists = True
    while exists:
        seed = random.randint(0, 2**32)
        eta = 0.0
        scale = random.sample([6,7,8,9,10,11,12,13,14], 1)[0]
        steps = 20
        sampler = "k_euler_ancestral"
        dream = getOldestDream()
        if type_seed <= 3 or not dream:
            # Hallucinate
            origin = "hallucination"
            author_id = 977198605221912616
            q = {
                "nsfw": {"$nin": [True]},
                "hide": {"$nin": [True]},
                "author_id": {"$nin" : [705873534798528572, 1017500241655762945, 747134662597541938, 598553498371751946, 543116602313408524, 1019374566008692738]},
                "origin": "web",
                "private" : False,
                "algo" : "stable"
            }
            # FD User renders
            amount = 1
            with db.get_database() as client:
                operations = [
                    {"$match": q},
                    {"$sample": {"size": int(amount)}},
                ]
                r = client.database.pieces.aggregate(operations)
                h = []
                for piece in r:
                    params = piece.get("params")
                    pr = params["prompt"]
                    p = pr.split(",")
                    w = p[random.randint(0, len(p)-1)]
                    h.append(w)
            
            # SD Discord Dump
            amount = 1
            with db.get_database() as client:
                operations = [
                    {"$sample": {"size": int(amount)}},
                ]
                r = client.database.sd_prompt_dump.aggregate(operations)
                for piece in r:
                    pr = piece.get("prompt")
                    p = pr.split(",")
                    w = p[random.randint(0, len(p)-1)]
                    h.append(w)
                prompt = ",".join(h)
        else:
            # Dream
            origin = "dream"
            if dream.get("count"):
                count = int(dream.get("count")) + 1
            else:
                count = 1
            with db.get_database() as client:
                client.database.userdreams.update_one({"author_id": dream.get("author_id")}, {"$set": {"last_used": datetime.utcnow(), "count": count}}, upsert=True)
            template = dream.get("prompt")
            author_id = dream.get("author_id")
            prompt = prompt_salad.make_random_prompt(amount=1, prompt_salad_path="prompt_salad", template=template)[0]

        prompt_hash = str(hashlib.sha256(prompt.encode('utf-8')).hexdigest())
        params = {
            "repo" : "a1111",
            "weights" : weights_hash,
            "n_samples" : 1,
            "prompt" : prompt,
            "seed" : seed,
            "steps": steps,
            "eta" : eta,
            "scale" : scale,
            "width_height" : width_height,
            "sampler" : sampler
        }
        ns_params = SimpleNamespace(**params)
        p = json.dumps(ns_params.__dict__, indent = 4)
        param_hash = str(hashlib.sha256(p.encode('utf-8')).hexdigest())
        with db.get_database() as client:
            j = client.database.vw_all.find_one({"uuid" : param_hash})
            if j:
                exists = True
            else:
                exists = False
    
    # Make Job
    timestamp = datetime.utcnow()
    newrecord = {
        "agent_id" : agent_info['agent_id'],
        "weights" : weights_hash,
        "uuid" : param_hash,
        "preferred_image" : param_hash,
        # "author" : 977198605221912616,
        "author" : author_id,
        "timestamp": timestamp,
        "hide" : False,
        "nsfw" : False,
        "private" : False,
        "status" : "processing",
        "origin" : origin,
        "prompt_hash" : prompt_hash,
        "algo" : "stable",
        "repo" : "a1111",
        "width_height" : width_height,
        "params" : ns_params.__dict__
    }
    with db.get_database() as client:
        add_queue(newrecord)
    # logger.info(newrecord)
    return newrecord

def pulse(agent_id):
    with db.get_database() as client:
        agentCollection = client.database.get_collection("agents")
        agentCollection.update_one({"agent_id": agent_id}, {"$set": {"last_seen": datetime.utcnow()}})

def agent_pulse(agent_info, mode):
    """Updates DB State of Agent"""
    repo = "sd"
    if "repo" in agent_info:
        repo = agent_info["repo"]
    with db.get_database() as client:
        client.database.agents.update_one({"agent_id": agent_info['agent_id']},
            {"$set": {
                "last_seen": datetime.utcnow(),
                "mode": mode,
                "idle_time": int(agent_info["idle_time"]),
                "bot_version": str(agent_info["bot_version"]),
                "gpu": agent_info["gpu_record"],
                "agent_version" : agent_info["agent_version"],
                "algo" : "stable",
                "repo" : repo,
                "start_time" : agent_info["start_time"],
                "boot_time" : agent_info["boot_time"],
                "free_space" : agent_info["free_space"],
                "used_space" : agent_info["used_space"],
                "total_space" : agent_info["total_space"],
                "memory" : agent_info["memory_record"]
                }
            }
        )


def agent_parse(agent_id, request):
    """Returns info about agent request for work"""
    idle_time = request.form.get("idle_time")
    bot_version = request.form.get("bot_version")
    agent_version = request.form.get("agent_version")
    start_time = request.form.get("start_time")
    boot_time = request.form.get("boot_time")
    try:
        repo = request.form.get("repo")
    except:
        repo = "sd"
    try:
        algo = request.form.get("algo")
    except:
        algo = "UNKNOWN"
    try:
        boot_time = datetime.strptime(boot_time, '%Y-%m-%d %H:%M:%S.%f')
    except:
        boot_time = None
    try:
        free_space = int(request.form.get("free_space"))
        used_space = int(request.form.get("used_space"))
        total_space = int(request.form.get("total_space"))
    except:
        free_space = 0
        used_space = 0
        total_space = 0
    try:
        m = request.form.get("memory")
        memory_record = json.loads(m)
    except:
        memory_record = request.form.get("memory")
    owner = request.form.get("owner")
    gpus = request.form.get("gpus")
    gpu_size = "small"
    if type(gpus) is str:
        try:
            gpu_record = json.loads(gpus)
            vram = gpu_record["mem_total"]
            if vram>13000:
                gpu_size = "medium"
            if vram>25000:
                gpu_size = "large"
            if vram>50000:
                gpu_size = "titan"
        except:
            gpu_record = None
    else:
        gpu_record = None

    return {
        "agent_id" : agent_id,
        "vram" : vram,
        "algo" : algo,
        "repo" : repo,
        "idle_time" : idle_time,
        "bot_version" : bot_version,
        "agent_version" : agent_version,
        "start_time" : start_time,
        "boot_time" : boot_time,
        "free_space" : free_space,
        "used_space" : used_space,
        "total_space" : total_space,
        "memory_record" : memory_record,
        "gpu_record" : gpu_record,
        "owner" : owner,
        "gpus" : gpus,
        "gpu_size" : gpu_size
    }

def v3_postProcess(job_uuid, algo, review):
    with db.get_database() as client:
        if review:
            pieces = client.database.reviews
        else:
            pieces = client.database.pieces
        
        job = pieces.find_one({"uuid": job_uuid})
        
        if algo == "disco":
            # TODO: get rid of "0_0" suffix
            # Inspect Document results
            # https://docarray.jina.ai/fundamentals/document/
            filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], job["filename"])
            png = os.path.join(current_app.config["UPLOAD_FOLDER"], f"{job_uuid}0_0.png")
            da = DocumentArray.load_binary(filepath)
            da[0].save_uri_to_file(png)
            da_tags = da[0].tags
            # logger.info(da_tags)
            # Annoyed that I can't figure this out.  Gonna write to filesystem
            # f = io.BytesIO(base64.b64decode(da[0].uri + '=='))
        
        if algo == "stable":
            png = os.path.join(current_app.config["UPLOAD_FOLDER"], f"{job_uuid}.png")

        
        
        ## Color Analysis
        color_thief = ColorThief(png)
        dominant_color = color_thief.get_color(quality=1)
        palette = color_thief.get_palette(color_count=5)

        pieces.update_one({"uuid": job_uuid}, {"$set": {"dominant_color": dominant_color, "palette": palette}})
        logger.info(f"🎨 Color analysis for {job_uuid} complete.")

        ## Indexing to Algolia
        if False:
            try:
                # TODO: Support array text_prompts
                algolia_index(job_uuid)
                pieces.update_one({"uuid": job_uuid}, {"$set": {"indexed": True}})
                logger.info(f"🔍 Job indexed to Algolia.")
            except:
                logger.info("Error trying to submit Algolia index.")
                pass
        
        ## Save thumbnails/jpg and upload to S3
        if current_app.config["BOT_USE_S3"]:
            logger.info(f"🌍Uploading files to S3 bucket {current_app.config['BOT_S3_BUCKET']}")
            try:
                # TODO: remove "0_0" suffix
                if algo == "disco":
                    upload_file_s3(png, current_app.config['BOT_S3_BUCKET'], f"images/{job_uuid}0_0.png", {"ContentType": "image/png"})
                
                if algo == "stable":
                    upload_file_s3(png, current_app.config['BOT_S3_BUCKET'], f"images/{job_uuid}.png", {"ContentType": "image/png"})
                
                s3_thumbnail(job_uuid, 64, algo=algo)
                s3_thumbnail(job_uuid, 128, algo=algo)
                s3_thumbnail(job_uuid, 256, algo=algo)
                s3_thumbnail(job_uuid, 512, algo=algo)
                s3_thumbnail(job_uuid, 1024, algo=algo)
                s3_jpg(job_uuid, algo=algo)
                pieces.update_one({"uuid": job_uuid}, {"$set": {"thumbnails": [64, 128, 256, 512, 1024], "jpg": True}})
                # logger.info(f"👍 Thumbnails uploaded to s3 for {job_uuid}")
                # logger.info(f"🖼️ JPEG version for {job_uuid} saved to s3")

            except Exception as e:
                logger.error(e)

            payload = {
                "status": "complete",
                "time_completed" : datetime.utcnow(),
                "results" : None    # TODO - Remove
            }
                            
            ## Mark as postprocessing complete
            if algo == "disco":
                payload["discoart_tags"] = da_tags
            
            pieces.update_one({"uuid": job_uuid}, {"$set": payload})