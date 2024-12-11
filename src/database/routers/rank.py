from bson import ObjectId
from pydantic import BaseModel, Field
from io import BytesIO
from fastapi import FastAPI
from pymongo import MongoClient
from collections import Counter
from typing import List
import json
import boto3
import pandas as pd
import datetime
import os
from dotenv import load_dotenv  # 추가

load_dotenv()  # .env 파일에서 변수 로드

app = FastAPI()

# MongoDB 연결
client = MongoClient(os.getenv('MONGO_URI'))
db = client["tut"]
collection = db["rank"]

aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
region_name=os.getenv("AWS_DEFAULT_REGION")

# S3에서 로그 읽기
s3_client = boto3.client('s3',
                        aws_access_key_id=aws_access_key_id,
                        aws_secret_access_key=aws_secret_access_key,
                        region_name=region_name
                        )

time_format = datetime.datetime.now()
timestamp = time_format.strftime("%Y-%m-%d_%H-%M-%S")

def get_logs(bucket_name: str = "t1-tu-data", directory: str = 'logs/') -> List[dict]:
    try:
        # S3에서 디렉토리 내 파일 목록 가져오기
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=directory)

        # 파일 목록을 가져왔는지 확인
        if 'Contents' not in response:
            print("No files found in the specified directory.")
            return []

        # Parquet 파일만 필터링
        parquet_files = [obj['Key'] for obj in response['Contents'] if obj['Key'].endswith('.parquet')]

        if not parquet_files:
            print("No Parquet files found.")
            return []

        # Parquet 파일을 읽어 pandas DataFrame으로 결합
        all_logs = []
        for file_key in parquet_files:
            try:
            # S3에서 Parquet 파일을 읽기
                print(f"Reading file: s3://{bucket_name}/{file_key}")
                obj = s3_client.get_object(Bucket=bucket_name, Key=file_key)
                # BytesIO를 사용하여 Parquet 파일을 pandas로 읽기
                parquet_data = BytesIO(obj['Body'].read())
                df = pd.read_parquet(parquet_data)  # pyarrow 또는 fastparquet 필요
                all_logs.append(df)
            except Exception as e:
                print(f"Error reading file {file_key}: {e}")

        if all_logs:
            combined_df = pd.concat(all_logs, ignore_index=True)
            logs = combined_df.to_dict(orient="records")
            return logs
        else:
            print("No valid data found in Parquet files")
            return []

    except Exception as e:
        print(f"Error reading from S3: {e}")
        return []

# FastAPI 라우터 정의
@app.get("/logs", response_model=List[dict])
async def get_rank():
    logs = get_logs()
    if not logs:
        return {"message": "No logs available or failed to fetch logs."}
    return logs

# Pydantic 모델 정의
class RankItem(BaseModel):
    id: str = Field(alias="_id")  # ObjectId를 문자열로 처리
    action: str
    clicks: int

    class Config:
        json_encoders = {
            ObjectId: str  # ObjectId를 문자열로 변환
        }

# MongoDB에 상위 클릭된 상품 저장
def save_rank_to_mongo(top_products: List[dict]):
    collection.delete_many({})  # 기존 데이터를 삭제하고 새로 저장
    collection.insert_many(top_products)

# MongoDB에서 상위 클릭된 상품 조회
def get_rank_from_mongo(top: int = 5) -> List[RankItem]:
    # MongoDB에서 데이터 조회 후 ObjectId를 문자열로 변환
    items = collection.find().limit(top)
    return [RankItem(**{**item, "_id": str(item["_id"])}) for item in items]

# FastAPI 라우터 정의
@app.get("/rank", response_model=List[RankItem])
async def get_rank(top: int = 5):
    # MongoDB에서 데이터 확인
    top_products = get_rank_from_mongo(top)
    if not top_products:  # MongoDB에 데이터가 없을 경우
        logs = get_logs()
        if not logs:  # logs가 없으면 에러 메시지와 함께 빈 리스트 반환
            print("No logs available or failed to fetch logs.")
            return []

        # Action Counter를 사용하여 클릭 수 집계
        action_counter = Counter()
        for log in logs:
            action = log.get('action')
            if action:
                action_counter[action] += 1

        # 상위 상품 생성
        top_products = [{"action": action, "clicks": count} for action, count in action_counter.most_common(top)]

        # MongoDB에 저장
        save_rank_to_mongo(top_products)

        # 저장된 데이터 Pydantic 모델로 변환
        top_products = get_rank_from_mongo(top)

    return top_products