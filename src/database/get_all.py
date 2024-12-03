from fastapi import FastAPI, Query
from pymongo import MongoClient
from typing import Optional

# MongoDB 연결
client = MongoClient("mongodb+srv://hahahello777:NDWdS4f47d3uLnZ3@cluster0.5vlv3.mongodb.net/test?retryWrites=true&w=majority&appName=Cluster0")
db = client['test']  # 데이터베이스 이름
collection = db['test']  # 컬렉션 이름

# FastAPI 애플리케이션 생성
app = FastAPI()

# Title로 검색
@app.get("/search/title")
def search_by_title(title: str = Query(...)):
    query = {"title": {"$regex": title, "$options": "i"}}
    results = list(collection.find(query, {"_id": 0}))
    return {"data": results}

# Category로 검색
@app.get("/search/category")
def search_by_category(category: str = Query(...)):
    query = {"category": category}
    results = list(collection.find(query, {"_id": 0}))
    return {"data": results}

# Start Date로 검색
@app.get("/search/start_date")
def search_by_start_date(start_date: str = Query(...)):
    query = {"start_date": start_date}
    results = list(collection.find(query, {"_id": 0}))
    return {"data": results}

# Artist Name으로 검색
@app.get("/search/artist_name")
def search_by_artist_name(artist_name: str = Query(...)):
    query = {"artist.artist_name": {"$regex": artist_name, "$options": "i"}}
    results = list(collection.find(query, {"_id": 0}))
    return {"data": results}


