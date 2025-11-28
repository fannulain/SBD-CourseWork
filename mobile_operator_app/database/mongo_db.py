import os
import pymongo
from bson.objectid import ObjectId
from dotenv import load_dotenv
from typing import List, Dict, Any
from datetime import datetime
from models import ServiceRequest

load_dotenv()

class MongoManager():
    def __init__(self):
        uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
        self.client = pymongo.MongoClient(uri)
        self.db = self.client["mobile_operator_coursework"]
        self.collection = self.db["service_requests"]

    def create_request(self, req: ServiceRequest) -> str:
        data = req.model_dump()
        result = self.collection.insert_one(data)
        return str(result.inserted_id)
    
    def get_all_requests(self, only_open: bool = True) -> List[Dict[str, Any]]:
        filter_query = {}
        if only_open:
            filter_query = {"status": "open"}

        cursor = self.collection.find(filter_query).sort("created_at", -1)

        results = []
        for doc in cursor:
            doc['id'] = str(doc['_id'])
            del doc['_id']
            results.append(doc)

        return results
    
    def get_requests_by_ric(self, ric: str) -> List[Dict[str, Any]]:
        cursor = self.collection.find({"ric": ric}).sort("created_at", -1)

        results = []
        for doc in cursor:
            doc['id'] = str(doc['_id'])
            del doc['_id']
            results.append(doc)

        return results
    
    def close_request(self, request_id: str):
        try:
            oid = ObjectId(request_id)

            self.collection.update_one(
                {"_id": oid},
                {
                    "$set": {
                        "status": "closed",
                        "closed_at": datetime.now()
                    }
                }
            )
            return True
        except Exception as e:
            print(f"Error closing request: {e}")
            return False
        
    def delete_request(self, request_id: str):
        try:
            oid = ObjectId(request_id)
            self.collection.delete_one({"_id": oid})
            return True
        except Exception as e:
            return False