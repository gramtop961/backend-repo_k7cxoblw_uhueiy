import os
from typing import Any, Dict, Optional, List
from datetime import datetime
from pymongo import MongoClient
from pymongo.collection import Collection

DATABASE_URL = os.getenv("DATABASE_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "app_db")

_client: MongoClient = MongoClient(DATABASE_URL)
db = _client[DATABASE_NAME]


def _collection(name: str) -> Collection:
    return db[name]


def create_document(collection_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
    now = datetime.utcnow()
    data_with_meta = {**data, "created_at": now, "updated_at": now}
    col = _collection(collection_name)
    res = col.insert_one(data_with_meta)
    inserted = col.find_one({"_id": res.inserted_id})
    if not inserted:
        raise RuntimeError("Failed to insert document")
    inserted["id"] = str(inserted.pop("_id"))
    return inserted


def get_documents(
    collection_name: str,
    filter_dict: Optional[Dict[str, Any]] = None,
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    col = _collection(collection_name)
    cursor = col.find(filter_dict or {})
    if limit:
        cursor = cursor.limit(limit)
    items: List[Dict[str, Any]] = []
    for doc in cursor:
        doc["id"] = str(doc.pop("_id"))
        items.append(doc)
    return items


def find_one(collection_name: str, filter_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    col = _collection(collection_name)
    doc = col.find_one(filter_dict)
    if not doc:
        return None
    doc["id"] = str(doc.pop("_id"))
    return doc


def update_one(collection_name: str, filter_dict: Dict[str, Any], update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    col = _collection(collection_name)
    update_data["updated_at"] = datetime.utcnow()
    res = col.find_one_and_update(filter_dict, {"$set": update_data}, return_document=True)
    if not res:
        return None
    res["id"] = str(res.pop("_id"))
    return res
