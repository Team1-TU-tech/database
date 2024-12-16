import pytz
from fastapi import APIRouter, Query, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from typing import List, Optional
from bson import ObjectId
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from src.database.routers.log_handler import *
import os
import certifi
from dotenv import load_dotenv

load_dotenv()  # .env 파일에서 변수 로드

mongo_uri = os.getenv("MONGO_URI")
router = APIRouter()

# MongoDB 연결을 위한 클라이언트
try:
    client = AsyncIOMotorClient(mongo_uri)
    db = client['tut']
    collection = db['ticket']
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


# 티켓 검색 API
@router.get("/search", response_model=List[TicketData])
# 1. jwt가 request header안에 있다는 가정하에, request header안에 있는 토큰을 열어본다
# 2. 토큰이 없다면 로그인 되지 않은 유저이므로 바로 anonymous 처리 한다
# 3. 토큰이 있다면 jwt.decode를 통해 토큰안에 담긴 user_id를 꺼내온다
# 4. user_id를 pymongo find_one("user_id":jwt.decode한 정보)로 필요한 유저 정보를 찾아온다
# 5. 필요한 정보를 로그파일에 담는다(유저 정보 및 어떤 api를 호출했는가 등등)
async def search_tickets(
    request: Request, # 요청 객체 추가
    keyword: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    
    #############로그데이터를 위한 로직 추가##############
    device = request.headers.get("User-Agent", "Unknown")
    ###############################################
    query = {}

    # 카테고리 매핑 적용
    if category:
        categories = category.split("/")
        query["category"] = {"$in": categories}

    if start_date:
        start_date = parse_date(start_date)
        if start_date:
            query["start_date"] = {"$lte": end_date}

    if end_date:
        end_date = parse_date(end_date)
        if end_date:
            query["end_date"] = {"$gte": start_date}

    if region:
        query["region"] = region

    if keyword:
        query["$or"] = [
                {"title": {"$regex": keyword, "$options": "i"}},
                {"artist.artist_name": {"$regex": keyword, "$options": "i"}}
                ]

    cursor = collection.find(query)
    print(f"MongoDB Query: {query}")
    # MongoDB에서 검색

    # 한국 시간(KST) 기준으로 오늘 날짜 구하기
    kst = pytz.timezone('Asia/Seoul')
    today_date = datetime.now(kst)
    today = datetime.strftime(today_date, "%Y.%m.%d")


    tickets = []
    async for ticket in cursor:
        hosts = ticket.get("hosts", [])
        isexclusive = len(hosts) <= 1
        ticket_url = any(host.get("ticket_url") is not None for host in hosts)
        end_date_str = ticket.get('end_date')
        try:
            ticket_end_date = datetime.strptime(end_date_str, "%Y.%m.%d").strftime("%Y.%m.%d")
            # ticket_url이 존재하고, end_date가 오늘 이후일 때만 on_sale을 True로 설정
            if ticket_url and ticket_end_date>=today:
                on_sale = True
            else:
                on_sale = False
        except (ValueError, TypeError) as e:
            print(f"Error parsing end_date: {e}")
            on_sale = False  # end_date 형식 오류시 on_sale은 False

        ticket_data = {
            "poster_url": ticket.get("poster_url"),
            "title": ticket.get("title"),
            "location": ticket.get("location"),
            "start_date": ticket.get("start_date"),
            "end_date": ticket.get("end_date"),
            "id": str(ticket.get("_id")),
            "isExclusive": isexclusive,
            "onSale": on_sale
        }
        tickets.append(ticket_data)
    
    try:  
        token = request.headers.get('Authorization', 'anonymous')
        token = token.split('bearer ')[1]
        if token == '':
            log_event(
                user_id='anonymous',  # 헤더에서 받은 user_id 사용
                gender='unknown',
                birthday='unknown',
                device=device,     # 디바이스 정보 (User-Agent 또는 쿼리 파라미터)
                action="search",   # 액션 종류: 'Search'
                topic="search_log", #카프카 토픽 구별을 위한 컬럼
                category=category if category is not None else "None", # 카테고리
                region=region if region is not None else "None",
                keyword=keyword if keyword is not None else "None"
                
            )
            print("Anonymous Log event should have been recorded.")
        else:
            decoded_token = verify_token(
                token=token,
                SECRET_KEY=os.getenv("SECRET_KEY"),
                ALGORITHM=os.getenv("ALGORITHM"),
                refresh_token=None,
                expires_delta=None
                )
        
            user = await user_collection.find_one({"id":decoded_token["id"]},{'_id': 0})
            log_event(
                user_id=user["id"],  # 헤더에서 받은 user_id 사용
                gender=user['gender'],
                birthday=user['birthday'],
                device=device,     # 디바이스 정보 (User-Agent 또는 쿼리 파라미터)
                action="search",   # 액션 종류: 'Search'
                topic="search_log", #카프카 토픽 구별을 위한 컬럼
                category=category if category is not None else "None", # 카테고리
                region=region if region is not None else "None",
                keyword=keyword if keyword is not None else "None"
            )
            print(f"{user["id"]} Log event should have been recorded.")

    except Exception as e:
        print(f"Error logging event: {e}")

    return tickets

# ID로 상세 조회
@router.get("/detail/{id}")
async def get_detail_by_id(request: Request, id: str):

    #############로그데이터를 위한 로직 추가##############
    device = request.headers.get("User-Agent", "Unknown")
    ###############################################

    try:
        object_id = ObjectId(id)
        result = await collection.find_one({"_id": object_id})

        if result:
            result['_id'] = str(result['_id'])
            
            log_event(
                user_id=user_id,  # 헤더에서 받은 user_id 사용
                device=device,     # 디바이스 정보 (User-Agent 또는 쿼리 파라미터)
                action="view_detail",   # 액션 종류: 'view_detail' (상세 조회)
                topic="view_detail_log", #카프카 토픽 구별을 위한 컬럼
                ticket_id= result['_id'],
                title= result['title'],
                category=result['category'] if result['category'] is not None else "None", # 카테고리
                region=result['region'] if result['region'] is not None else "None",     # 지역
                )
            
            return {"data": result}
        else:
            raise HTTPException(status_code=404, detail="Item not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid ObjectId format")

