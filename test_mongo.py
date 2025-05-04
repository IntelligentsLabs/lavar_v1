from pymongo import MongoClient
import bson
import os

# Setup
objId = bson.objectid.ObjectId
uri = "mongodb+srv://cclarke411:Blackpanther2614@cluster0.feozg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

if not uri:
    raise EnvironmentError("MONGO_URI environment variable not set!")

# Connect to MongoDB
client = MongoClient(uri)
main = client.appdb
Users = main.users


# Functions
def get_user_by_email(email):
    return Users.find_one({"email": email})


def check_if_user_exists(email):
    user = get_user_by_email(email)
    return user is not None


# Main check
if __name__ == "__main__":
    email_to_check = "clyde.clarke@gmail.com"
    exists = check_if_user_exists(email_to_check)

    if exists:
        print(f"✅ User with email '{email_to_check}' exists in the database.")
    else:
        print(
            f"❌ User with email '{email_to_check}' does NOT exist in the database."
        )
