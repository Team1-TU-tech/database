from fastapi import APIRouter, Query, HTTPException, Request
from typing import List, Optional
from bson import ObjectId
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from database.routers.log_handler import *

# MongoDB 연결을 위한 클라이언트
try:
    client = AsyncIOMotorClient("mongodb+srv://summerham22:FEm4DxNh3oxLK3rM@cluster0.5vlv3.mongodb.net/test?retryWrites=true&w=majority&appName=Cluster0")
    db = client['test']
    collection = db['test']
    print("MongoDB connected successfully!")

except Exception as e:
    print(f"MongoDB connection error: {e}")

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
    request: Request, # 요청 객체 추가
    keyword: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    
    #############로그데이터를 위한 로직 추가##############
     # 현재 시간 자동 추출
    current_timestamp = datetime.now().isoformat()
    device = request.headers.get("User-Agent", "Unknown")
    user_id = request.headers.get("user_id", "anonymous")  # user_id가 없으면 "anonymous"로 기본값 설정
    ###############################################
    
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
    print(f"MongoDB Query: {query}")
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
    
    try:
        log_event(
            current_timestamp=current_timestamp,
            user_id=user_id,  # 헤더에서 받은 user_id 사용
            device=device,     # 디바이스 정보 (User-Agent 또는 쿼리 파라미터)
            action="Search",   # 액션 종류: 'Search'
            category=category, # 카테고리
            region=region,     # 지역
            keyword=keyword
            
    )
    except Exception as e:
        print(f"Error logging event: {e}")


    print("Log event should have been recorded.")

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

