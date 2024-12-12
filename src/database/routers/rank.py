from bson import ObjectId
from pydantic import BaseModel, Field, ValidationError
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

def get_logs(bucket_name: str = "t1-tu-data", directory: str = 'view_detail_log/') -> List[dict]:
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

# Pydantic 모델 정의
class RankItem(BaseModel):
    ticket_id: str
    clicks: int

# MongoDB에서 상위 클릭된 상품 조회
def get_rank_from_mongo(top: int = 8) -> List[RankItem]:
    # MongoDB에서 데이터 조회 후 ObjectId를 문자열로 변환
    items = collection.find().limit(top)
    valid_items = []
    for item in items:
        try:
            # 필요한 필드가 모두 있는 경우에만 RankItem으로 변환
            valid_item = RankItem(**{
                "ticket_id": item.get("ticket_id", "unknown"),  # 기본값 설정
                "clicks": item.get("clicks", 0)  # 기본값 설정
            })
            valid_items.append(valid_item)
        except ValidationError as e:
            print(f"Validation failed for item {item}: {e}")
    return valid_items

# FastAPI 라우터 정의
@app.get("/rank", response_model=List[RankItem])
async def get_rank(top: int = 8):
    # MongoDB에서 데이터 확인
    top_products = get_rank_from_mongo(top)
    if not top_products:  # MongoDB에 데이터가 없을 경우
        logs = get_logs()
        if not logs:  # logs가 없으면 에러 메시지와 함께 빈 리스트 반환
            print("No logs available or failed to fetch logs.")
            return []

        logs_df = pd.DataFrame(logs)

        if 'ticket_id' in logs_df.columns:
            count_df = logs_df.groupby('ticket_id').size().reset_index(name='clicks')
            top_products = count_df.nlargest(top, 'clicks').to_dict('records')
        else:
            print("No 'ticket_id' column in logs.")
            return []

        # 저장된 데이터 Pydantic 모델로 변환
        top_products = get_rank_from_mongo(top)

    return top_products
