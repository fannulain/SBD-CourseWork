import os
import redis
import json
from dotenv import load_dotenv
from typing import List, Optional
from .models import DebtorReport

load_dotenv()

class RedisManager:
    def __init__(self):
        host = os.getenv("REDIS_HOST", "localhost")
        port = int(os.getenv("REDIS_PORT", 6379))

        self.r = redis.Redis(
            host=host, 
            port=port, 
            db=0, 
            decode_responses=True
        )
        self.cache_key = "debtors_cache"
        self.ttl_seconds = 3600

    def cache_debtors(self, debtors: List[DebtorReport]):
        self.r.delete(self.cache_key)

        if not debtors:
            return
        
        json_data = [d.model_dump_json() for d in debtors]
        self.r.rpush(self.cache_key, *json_data)
        self.r.expire(self.cache_key, self.ttl_seconds)

    def get_cached_debtors(self) -> List[DebtorReport]:
        if not self.r.exists(self.cache_key):
            return []
        
        raw_data = self.r.lrange(self.cache_key, 0, -1)

        debtors_list = []
        for item in raw_data:
            try:
                data_dict = json.loads(item)
                
                obj = DebtorReport(**data_dict)
                debtors_list.append(obj)
            except Exception as e:
                print(f"Error: {e}")
        
        return debtors_list
    
    def clear_cache(self):
        self.r.delete(self.cache_key)