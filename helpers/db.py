from pymongo import MongoClient
from config import MONGO_URI
from helpers.db import users_collection
client = MongoClient(MONGO_URI)
db = client['quiz_bot']
users_collection = db['users']
