from fastapi import FastAPI, Query
from pymongo import MongoClient
from bson.objectid import ObjectId
from dotenv import load_dotenv
import os

load_dotenv()  # .env 파일에서 변수 로드

app = FastAPI()

# MongoDB 연결
client = MongoClient(os.getenv('MONGO_URI'))
db = client["test"]
collection = db["similar"]

@app.get("/recommandation")
async def get_similar_performances(title: str = Query(...)):
    
    # MongoDB에서 특정 title이 있는 문서 찾기
    document = collection.find_one({"similar_performances.title":"_id" })
    
    if not document:
        return {"message": f"No performances found for title: {_id}"}

    # 결과를 저장할 리스트
    result = []

    # 해당 title에 대한 ID 찾기
    for performance in document.get("similar_performances", []):
        if performance.get("title") == title:
            current_id = str(performance["_id"])
            result.append({
                "id": current_id,
                "title": performance.get("title"),
                "start_date": performance.get("start_date"),
                "end_date": performance.get("end_date"),
                "location": performance.get("location")  
            })

            # 해당 title을 제외한 다른 3가지 similar_performances 추가
            similar_performances = [
                {
                    "id": str(item["_id"]),
                    "title": item.get("title"),
                    "start_date": item.get("start_date"),
                    "end_date": item.get("end_date"),
                    "location": item.get("region")
                }
                for item in document.get("similar_performances", [])
                if item.get("title") != title
            ][:3]  # 최대 3개까지만 선택

            result.extend(similar_performances)
            break

    return {"performances": result}

