from fastapi import FastAPI, Query
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional, List
from bson import ObjectId

# FastAPI 애플리케이션 객체 생성
app = FastAPI()

# MongoDB 연결을 위한 클라이언트
client = AsyncIOMotorClient("mongodb+srv://hahahello777:NDWdS4f47d3uLnZ3@cluster0.5vlv3.mongodb.net/test?retryWrites=true&w=majority&appName=Cluster0")  # MongoDB 연결 URL (로컬 MongoDB)
db = client['test']  # 데이터베이스 이름
collection = db['test']  # 컬렉션 이름

# Pydantic 모델 정의 (응답 형식)
class TicketData(BaseModel):
    poster_url: Optional[str]
    title: Optional[str]
    location: Optional[str]
    start_date: Optional[str]
    end_date: Optional[str]


# API 엔드포인트 정의
@app.get("/search", response_model=List[TicketData])
async def search_tickets(
    title: Optional[str] = Query(None, alias="title"),
    category: Optional[str] = Query(None, alias="category"),
    region: Optional[str] = Query(None, alias="region"),
    start_date: Optional[str] = Query(None, alias="start_date"),
):

    # MongoDB 쿼리 조건 설정
    query = {}
    
    if title:
        query["title"] = {"$regex": title, "$options": "i"}  # 대소문자 구분 없이 검색
    if category:
        query["category"] = {"$regex": category, "$options": "i"}
    if region:
        query["region"] = {"$regex": region, "$options": "i"}
    if start_date:
        query["start_date"] = {"$regex": start_date, "$options": "i"}
    
    # MongoDB에서 쿼리 실행
    cursor = collection.find(query)
    
    # 결과 반환
    tickets = []
    async for ticket in cursor:
        ticket_data = {
            "poster_url": ticket.get("poster_url"),
            "title": ticket.get("title"),
            "location": ticket.get("location"),
            "start_date": ticket.get("start_date"),
            "end_date": ticket.get("end_date"),
        }
        tickets.append(ticket_data)
    
    return tickets
