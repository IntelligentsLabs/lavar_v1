from pymongo import MongoClient
import ssl
from os import getenv
from pymongo.server_api import ServerApi
import bson
import os

# Create a new client and connect to the server
objId = bson.objectid.ObjectId

uri = "mongodb+srv://cclarke411:Blackpanther2614@cluster0.feozg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# Create a new client and connect to the server
client = MongoClient(uri)
main = client.appdb
# User collection
Users = main.users


def get_user_by_email(email):
    return Users.find_one({"email": email})


def get_user_by_id(id):
    return Users.find_one({"_id": objId(id)})


def check_if_user_exists(email):
    user = get_user_by_email(email)
    if user:
        return True
    else:
        return False


def create_user(user):
    return Users.insert_one(user)


def add_color_to_user(color, user_id):
    return Users.update_one({'_id': objId(user_id)},
                            {'$set': {
                                'current_bg': color
                            }})


def change_char(changes, user_id):
    if 'powers' in changes:
        Users.update_one({'_id': objId(user_id)},
                         {'$push': {
                             'character.powers': changes['powers']
                         }})

    elif 'equipments' in changes:
        Users.update_one(
            {'_id': objId(user_id)},
            {'$push': {
                'character.equipments': changes['equipments']
            }})

    else:
        Users.update_one({'_id': objId(user_id)}, {'$set': changes})
    return True
