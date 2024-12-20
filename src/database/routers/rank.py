from bson import ObjectId
from fastapi import FastAPI, HTTPException, APIRouter
from pymongo import MongoClient
from collections import Counter
from typing import List
from io import BytesIO
import boto3
import pandas as pd
import datetime
import os
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()

# FastAPI 앱 및 라우터 초기화
router = APIRouter()

# MongoDB 연결
client = MongoClient(os.getenv('MONGO_URI'))
db = client["tut"]
ticket_collection = db["ticket"]
popular_collection = db["popular"]

# AWS S3 클라이언트 설정
aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
region_name = os.getenv('AWS_DEFAULT_REGION')

s3_client = boto3.client(
    's3',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name=region_name
)

# S3에서 로그 데이터를 읽어오는 함수
def get_logs(bucket_name: str = "t1-tu-data", directory: str = 'view_detail_log/') -> List[str]:
    try:
        paginator = s3_client.get_paginator('list_objects_v2')
        operation_parameters = {'Bucket': bucket_name, 'Prefix': directory}
        parquet_files = []

        for page in paginator.paginate(**operation_parameters):
            if 'Contents' in page:
                page_files = [obj['Key'] for obj in page['Contents'] if obj['Key'].endswith('.parquet')]
                parquet_files.extend(page_files)

        if not parquet_files:
            print("No Parquet files found.")
            return []

        logs = []
        for file_key in parquet_files:
            try:
                print(f"Reading file: s3://{bucket_name}/{file_key}")
                obj = s3_client.get_object(Bucket=bucket_name, Key=file_key)
                parquet_data = BytesIO(obj['Body'].read())
                df = pd.read_parquet(parquet_data)
                logs.append(df)
            except Exception as e:
                print(f"Error reading file {file_key}: {e}")

        all_logs = pd.concat(logs, ignore_index=True)
        ticket_ids = all_logs['ticket_id'].tolist()

        return ticket_ids

    except Exception as e:
        print(f"Error reading from S3: {e}")
        return []

# MongoDB에 인기 티켓 정보를 저장하는 함수
def save_popular_to_db(ticket_ids: List[str]):
    try:
        ticket_counter = Counter(ticket_ids)
        sorted_tickets = [{"ticket_id": ticket_id, "count": count} for ticket_id, count in ticket_counter.most_common()]

        popular_collection.delete_many({})
        popular_collection.insert_many(sorted_tickets)
        print("Popular collection updated.")
    except Exception as e:
        print(f"Error updating popular collection: {e}")

# API로 인기 티켓 정보를 반환하는 함수
@router.get("/top_show")
async def get_top_tickets():
    ###########################################
    ticket_ids = get_logs()
    if not ticket_ids:
        print("No logs found")
    save_popular_to_db(ticket_ids)
    ###########################################
    current_date = datetime.datetime.now()
    popular_tickets = list(popular_collection.find())

    if not popular_tickets:
        raise HTTPException(status_code=404, detail="No popular tickets found")

    filtered_tickets = []
    for ticket in popular_tickets:
        ticket_data = ticket_collection.find_one({"_id": ObjectId(ticket['ticket_id'])})
        if ticket_data:
            start_date = datetime.datetime.strptime(ticket_data.get("start_date", ""), "%Y.%m.%d")
            end_date = datetime.datetime.strptime(ticket_data.get("end_date", ""), "%Y.%m.%d")

            # 날짜 조건 필터링
            if start_date >= current_date and end_date > current_date:
                ticket_info = {
                    "id": str(ticket_data['_id']),
                    "title": ticket_data.get("title", ""),
                    "start_date": ticket_data.get("start_date", ""),
                    "end_date": ticket_data.get("end_date", ""),
                    "poster_url": ticket_data.get("poster_url", ""),
                    "location": ticket_data.get("location", "")
                }
                filtered_tickets.append(ticket_info)

    if not filtered_tickets:
        raise HTTPException(status_code=404, detail="No tickets match the date criteria")

    # 상위 8개 결과만 반환
    return {"top_tickets": filtered_tickets[:8]}

# 로그 데이터를 처리하고 DB를 업데이트하는 함수
#def process_and_update_popular():
#    ticket_ids = get_logs()
#    if not ticket_ids:
#        print("No logs found.")
#        return
#
#    save_popular_to_db(ticket_ids)


