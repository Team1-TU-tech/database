from bson import ObjectId
from pydantic import BaseModel, Field
from io import BytesIO
from fastapi import FastAPI
from pymongo import MongoClient
from collections import Counter
from typing import List, Dict
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
collection = db["ticket"]

aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
region_name=os.getenv("AWS_DEFAULT_REGION")

# S3에서 로그 읽기
s3_client = boto3.client('s3',
                        aws_access_key_id=aws_access_key_id,
                        aws_secret_access_key=aws_secret_access_key,
                        region_name=region_name
                        )

@app.get("/top10", response_model=List[Dict[str, int]])
async def get_top10(bucket_name: str = "t1-tu-data", directory: str = 'view_detail_log/'):
    try:
        # S3에서 디렉토리 내 파일 목록 가져오기
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=directory)
        print(response)

        # 파일 목록을 가져왔는지 확인
        if 'Contents' not in response:
            return []

        # Parquet 파일만 필터링
        parquet_files = [obj['Key'] for obj in response.get('Contents', []) if obj['Key'].endswith('.parquet')]
        all_logs = []

        # 모든 Parquet 파일 읽기
        for file_key in parquet_files:
            obj = s3_client.get_object(Bucket=bucket_name, Key=file_key)
            parquet_data = BytesIO(obj['Body'].read())
            df = pd.read_parquet(parquet_data)
            all_logs.append(df)

        if all_logs:
            # 데이터 결합 및 ticket_id 카운트
            df_all = pd.concat(all_logs, ignore_index=True)
            ticket_counts = df_all['ticket_id'].value_counts().sort_values(ascending=False)
            top_tickets = ticket_counts.head(8)
            
            # MongoDB에서 ticket_id에 해당하는 데이터를 가져오기
            ticket_details = []
            for ticket_id in top_tickets.index:
                # ticket_id를 ObjectId로 변환하여 MongoDB에서 조회
                ticket_data = collection.find_one({'_id': ObjectId(ticket_id)})
                if ticket_data:
                    ticket_details.append({
                        'ticket_id': str(ticket_data['_id']),
                        'count': top_tickets[ticket_id],
                        'ticket_info': ticket_data
                    })

            return ticket_details
        else:
            return []

    except Exception as e:
        print(f"Error occurred: {e}")
        return []
