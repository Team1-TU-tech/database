from fastapi import FastAPI, Query
from pymongo import MongoClient
from typing import Optional

# MongoDB 연결
client = MongoClient("mongodb+srv://hahahello777:akXSTBrO5Q5OkWb3@cluster0.5vlv3.mongodb.net/test?retryWrites=true&w=majority&appName=Cluster0")
db = client['test']  # 데이터베이스 이름
collection = db['test']  # 컬렉션 이름

# FastAPI 애플리케이션 생성
app = FastAPI()

# 특정 필드로 검색하는 엔드포인트
@app.get("/search")
def search_data(
    title: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    #region: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    artist_name: Optional[str] = Query(None),
):
    # 검색 조건 구성
    query = {}
    if title:
        query["title"] = {"$regex": title, "$options": "i"}  # 대소문자 구분 없이 부분 검색
    if category:
        query["category"] = category  # 정확히 일치
    #if region:
    #    query["region"] = region  # 정확히 일치
    if start_date:
        query["start_date"] = start_date  # 정확히 일치
    if artist_name:
        query["artist.artist_name"] = {"$regex": artist_name, "$options": "i"}  # 대소문자 구분 없이 부분 검색

    # MongoDB 검색
    results = list(collection.find(query, {"_id": 0}))  # "_id": 0으로 _id 필드 제외
    return {"data": results}

