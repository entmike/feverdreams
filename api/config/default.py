import os

UPLOAD_FOLDER=os.getenv("UPLOAD_FOLDER","../images")
PROFANITY_THRESHOLD=os.getenv("PROFANITY_THRESHOLD", 0.8)
STEP_LIMIT=os.getenv("STEP_LIMIT", 150)            # I think this is obsolete
AUTHOR_LIMIT=os.getenv("AUTHOR_LIMIT", 100)        # I think this is obsolete
MONGODB_CONNECTION=os.getenv("MONGODB_CONNECTION", "mongodb://localhost")
MAX_DREAM_OCCURENCE=os.getenv("MAX_DREAM_OCCURENCE",20)
AUTH0_DOMAIN=os.getenv("AUTH0_DOMAIN","dev-yqzsn326.auth0.com")
AUTH0_API_AUDIENCE=os.getenv("AUTH0_API_AUDIENCE","https://api.feverdreams.app/")
BOT_USE_S3=os.getenv("BOT_USE_S3",True)
BOT_S3_BUCKET=os.getenv("BOT_S3_BUCKET","devimages.feverdreams.app")
BOT_S3_WEB=os.getenv("BOT_S3_WEB","http://devimages.feverdreams.app.s3-website-us-east-1.amazonaws.com/images/")