from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
from bson import ObjectId
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

# MongoDB 연결을 위한 클라이언트
client = AsyncIOMotorClient("mongodb+srv://hahahello777:NDWdS4f47d3uLnZ3@cluster0.5vlv3.mongodb.net/test?retryWrites=true&w=majority&appName=Cluster0")
db = client['test']
collection = db['test']

# Pydantic 모델 정의
class TicketData(BaseModel):
    poster_url: Optional[str]
    title: Optional[str]
    location: Optional[str]
    start_date: Optional[str]
    end_date: Optional[str]
    id: str
    isExclusive: bool
    onSale: bool

# 날짜 문자열을 datetime 객체로 변환하는 함수
def parse_date(date_string: str) -> Optional[datetime]:
    try:
        return datetime.strptime(date_string, "%Y.%m.%d").strftime("%Y.%m.%d")
    except ValueError:
        return None

router = APIRouter()

# 티켓 검색 API
@router.get("/search", response_model=List[TicketData])
async def search_tickets(
    keyword: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    query = {}

    if start_date:
        start_date = parse_date(start_date)
        if start_date:
            query["start_date"] = {"$lte": end_date}

    if end_date:
        end_date = parse_date(end_date)
        if end_date:
            query["end_date"] = {"$gte": start_date}

    if category:
        query["category"] = category

    if region:
        query["region"] = region

    if keyword:
        query["$or"] = [
                {"title": {"$regex": keyword, "$options": "i"}},
                {"artist.artist_name": {"$regex": keyword, "$options": "i"}}
                ]

    cursor = collection.find(query)
    tickets = []
    async for ticket in cursor:
        hosts = ticket.get("hosts", [])
        isexclusive = len(hosts) <= 1
        ticket_url = any(host.get("ticket_url") is not None for host in hosts)
        ticket_data = {
            "poster_url": ticket.get("poster_url"),
            "title": ticket.get("title"),
            "location": ticket.get("location"),
            "start_date": ticket.get("start_date"),
            "end_date": ticket.get("end_date"),
            "id": str(ticket.get("_id")),
            "isExclusive": isexclusive,
            "onSale": ticket_url
        }
        tickets.append(ticket_data)

    return tickets

# ID로 상세 조회
@router.get("/detail/{id}")
async def get_detail_by_id(id: str):
    try:
        object_id = ObjectId(id)
        result = await collection.find_one({"_id": object_id})

        if result:
            result['_id'] = str(result['_id'])
            return {"data": result}
        else:
            raise HTTPException(status_code=404, detail="Item not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid ObjectId format")

