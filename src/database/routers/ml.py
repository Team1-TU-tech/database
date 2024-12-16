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

@app.get("/performances", summary="Get performances by title")
async def get_similar_performances(title: str = Query(..., description="Title to filter performances")):
    """
    특정 title 값을 기반으로 문서를 조회하고,
    해당 title에 대한 ID와 관련된 3가지 similar performances를 반환합니다.
    """
    # MongoDB에서 특정 title이 있는 문서 찾기
    document = collection.find_one({"similar_performances.title": title})
    
    if not document:
        return {"message": f"No performances found for title: {title}"}

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
                "location": performance.get("region")  # 'region' 필드를 location으로 사용
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

