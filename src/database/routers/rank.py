from fastapi import FastAPI, HTTPException, APIRouter
from pymongo import MongoClient
from bson import ObjectId
from pydantic import BaseModel
from typing import List, Optional
import datetime
from dotenv import load_dotenv
import os

load_dotenv()
router = APIRouter()

# MongoDB 클라이언트 설정
client = MongoClient(os.getenv("MONGO_URI"))
db = client["tut"]

# 컬렉션 참조
popular_collection = db["popular"]
collection = db["ticket"]

class TicketData(BaseModel):
    id: str
    title: str
    poster_url: str
    start_date: str
    end_date: str
    location: str

@router.get("/popular", response_model=List[TicketData])
async def get_popular_data():
    try:
        # tut_popular 데이터 가져오기 (count 기준 내림차순 정렬 후 상위 8개 선택)
        popular_docs = list(popular_collection.find({}, {"ticket_id": 1, "count": 1}).sort("count", -1).limit(8))

        # ticket_id 리스트 추출
        ticket_ids = [ObjectId(doc["ticket_id"]) for doc in popular_docs if "ticket_id" in doc]
        
        # 티켓 데이터를 한 번에 가져오기
        tickets = list(collection.find({"_id": {"$in": ticket_ids}}))

        # Pydantic 모델로 변환
        popular = [
            TicketData(
                id=str(ticket["_id"]),
                title=ticket.get("title", "Unknown Title"),
                poster_url=ticket.get("poster_url", ""),
                start_date=ticket.get("start_date", "Unknown Start Date"),
                end_date=ticket.get("end_date", "Unknown End Date"),
                location=ticket.get("location", "Unknown Location")
            )
            for ticket in tickets
        ]

        return popular

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

