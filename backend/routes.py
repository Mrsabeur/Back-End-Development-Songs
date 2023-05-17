from . import app
import os
import json
from flask import jsonify, request, make_response, abort, url_for  # noqa; F401
from pymongo import MongoClient
from bson import json_util
from pymongo.errors import OperationFailure
from pymongo.results import InsertOneResult
from bson.objectid import ObjectId
import sys

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "songs.json")
songs_list: list = json.load(open(json_url))

# client = MongoClient(
#     f"mongodb://{app.config['MONGO_USERNAME']}:{app.config['MONGO_PASSWORD']}@localhost")
mongodb_service = os.environ.get('MONGODB_SERVICE')
mongodb_username = os.environ.get('MONGODB_USERNAME')
mongodb_password = os.environ.get('MONGODB_PASSWORD')
mongodb_port = os.environ.get('MONGODB_PORT')

print(f'The value of MONGODB_SERVICE is: {mongodb_service}')

if mongodb_service == None:
    app.logger.error('Missing MongoDB server in the MONGODB_SERVICE variable')
    # abort(500, 'Missing MongoDB server in the MONGODB_SERVICE variable')
    sys.exit(1)

if mongodb_username and mongodb_password:
    url = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_service}"
else:
    url = f"mongodb://{mongodb_service}"


print(f"connecting to url: {url}")

try:
    client = MongoClient(url)
except OperationFailure as e:
    app.logger.error(f"Authentication error: {str(e)}")

db = client.songs
db.songs.drop()
db.songs.insert_many(songs_list)

def parse_json(data):
    return json.loads(json_util.dumps(data))

######################################################################
# INSERT CODE HERE
######################################################################

@app.route("/health")
def health():
    return {"status": "OK"}, 200

@app.route("/count")
def count():
    return {"count": len(songs_list)}, 200

@app.route("/song", methods=["GET"])
def songs():
    all_songs = db.songs.find({})
    songs = [song for song in all_songs]
    return json.dumps({"songs": songs}, default=str), 200

@app.route("/song/<id>", methods=["GET"])
def get_song_by_id(id):
    song = db.songs.find_one({"id": int(id)})
    if song:
        return json.dumps(song, default=str), 200
    else:
        return {"message": "song with id not found"}, 404

@app.route("/song", methods=["POST"])
def create_song():
    data = request.json

    for song in songs_list:
        if song["id"] == data["id"]:
            return {"Message": "song with id {} already present".format(song['id'])}, 302
    
    songs_list.append(data)
    result = db.songs.insert_one(data)
    return json.dumps({"inserted id": {"$oid": str(result.inserted_id)}}, default=str), 201

@app.route("/song/<int:id>", methods=["PUT"])
def update_song(id):
    data = request.json

    song = db.songs.find_one({"id": id})

    if song:
        if (song["lyrics"] != data["lyrics"] or song["title"] != data["title"]):
            result = db.songs.update_one({"id": id}, {"$set": {"lyrics": data["lyrics"], "title": data["title"]}})
            song = db.songs.find_one({"id": id})
            return json.dumps(song, default=str), 201
        else:
            return {"message":"song found, but nothing updated"}, 200
    return {"message": "song not found"}, 404

@app.route("/song/<int:id>", methods=["DELETE"])
def delete_song(id):
    result = db.song.delete_one({"id": id})
    if result.deleted_count == 0:
        return {"message": "song not found"}, 404
    else:
        return "", 204

