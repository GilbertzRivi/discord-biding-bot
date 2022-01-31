from pymongo import MongoClient

cluster = "mongodb://localhost:27017/?readPreference=primary&appname=MongoDB%20Compass&directConnection=true&ssl=false"
mongoc = MongoClient(cluster)
database = mongoc.bot_nft