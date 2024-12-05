from kafka import KafkaConsumer
import json
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import boto3
import os
from io import BytesIO
from dotenv import load_dotenv

# .env 파일을 로드하여 환경 변수 읽기
load_dotenv()

KAFKA_SERVER = os.getenv("KAFKA_SERVER", "kafka:9092")

# Kafka consumer 설정
consumer = KafkaConsumer(
    'logs',
    bootstrap_servers=KAFKA_SERVER,
    group_id='log-consumer-group',
    enable_auto_commit=False,  # 수동 오프셋 커밋 설정
    auto_offset_reset='earliest',  # 'earliest' 또는 'latest' 설정
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

# S3 클라이언트 설정
s3 = boto3.client('s3',
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name="ap-northeast-2"
    )

# 로그 데이터 소비 및 S3에 저장
def consume_and_save_to_s3():
    for message in consumer:
        log_message = message.value
        
        # 로그 메시지를 pandas DataFrame으로 변환
        df = pd.json_normalize(log_message)  # JSON을 DataFrame으로 변환

        # DataFrame을 Parquet 형식으로 변환
        table = pa.Table.from_pandas(df)
        
        # 메모리 버퍼에 Parquet 파일을 저장
        buffer = BytesIO()
        pq.write_table(table, buffer)
        buffer.seek(0)  # 버퍼의 처음으로 이동
        
        # S3에 Parquet 파일 업로드
        timestamp = log_message['timestamp'].replace(":", "-")  # timestamp로 파일명 생성
        s3.put_object(
            Bucket='t1-tu-data',
            Key=f'logs/{timestamp}.parquet',
            Body=buffer
        )

        print(f'로그가 S3에 업로드되었습니다: logs/{timestamp}.parquet')

        consumer.commit()  # 메시지를 처리한 후 수동으로 커밋

consume_and_save_to_s3()

