from flask import Flask
import random
from docarray import Document
from docarray import DocumentArray
from types import SimpleNamespace
import http.client
import urllib.parse
from email.policy import default
import re
from io import BytesIO, StringIO
from operator import truediv
from turtle import color, width
from pydotted import pydot
import requests
import jsbeautifier
import os, sys
from webbrowser import get
from flask import Flask, flash, request, redirect, url_for, jsonify, send_file
from flask_cors import CORS, cross_origin
from dotenv import load_dotenv
from yaml import dump, full_load
from werkzeug.utils import secure_filename
import hashlib
from datetime import datetime, timedelta
from bson import Binary, Code
from bson.json_util import dumps
from json import loads
import uuid
import json
from loguru import logger
from PIL import Image
import boto3
import botocore.exceptions
from functools import wraps
from jose import jwt
from flask import _request_ctx_stack
from colorthief import ColorThief
# from .utils.auth_utils import *
from .landingpage import landingpage
from .feeds import popular, recentlikes, recent, random, userfeed, following
from .security import myinfo, mypermissions
from .personal import myfavorites, personalfeed, myreviews, deletedfeed, myinvites, myjobs
from .widgets import tags, user, job, gpustats, queue
from .actions import follow, reportnsfw, pin, review, delete, undelete, create, review_personal, rolldice, update

app = Flask(__name__, instance_relative_config=True)
# Load the default configuration
app.config.from_object('config.default')

# Load the configuration from the instance folder
app.config.from_pyfile('config.py')

CORS(app)

# Landing Page
app.register_blueprint(landingpage)

# Widgets
app.register_blueprint(tags.blueprint)
app.register_blueprint(user.blueprint)
app.register_blueprint(job.blueprint)
app.register_blueprint(gpustats.blueprint)
app.register_blueprint(queue.blueprint)

# Feeds
app.register_blueprint(recent.blueprint)
app.register_blueprint(recentlikes.blueprint)
app.register_blueprint(random.blueprint)
app.register_blueprint(popular.blueprint)
app.register_blueprint(userfeed.blueprint)
app.register_blueprint(following.blueprint)

# Security
app.register_blueprint(myinfo.blueprint)
app.register_blueprint(mypermissions.blueprint)

# Personal
app.register_blueprint(myfavorites.blueprint)
app.register_blueprint(personalfeed.blueprint)
app.register_blueprint(myreviews.blueprint)
app.register_blueprint(deletedfeed.blueprint)
app.register_blueprint(myinvites.blueprint)
app.register_blueprint(myjobs.blueprint)

# Actions
app.register_blueprint(follow.blueprint)
app.register_blueprint(reportnsfw.blueprint)
app.register_blueprint(pin.blueprint)
app.register_blueprint(review.blueprint)
app.register_blueprint(review_personal.blueprint)
app.register_blueprint(undelete.blueprint)
app.register_blueprint(create.blueprint)
app.register_blueprint(update.blueprint)
app.register_blueprint(delete.blueprint)
app.register_blueprint(rolldice.blueprint)