from kafka import KafkaConsumer
import json
import boto3
from botocore.exceptions import NoCredentialsError
import os
from datetime import datetime

# Kafka Consumer 설정
KAFKA_BROKER = "localhost:9092"
KAFKA_TOPIC = "logs"
consumer = KafkaConsumer(
    KAFKA_TOPIC,
    bootstrap_servers=KAFKA_BROKER,
    value_deserializer=lambda x: json.loads(x.decode('utf-8')),
    group_id="log-consumers"
)

# S3 설정
AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
S3_BUCKET = 'your-s3-bucket-name'

# S3 클라이언트 생성
s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY
)

def save_log_to_s3(log_data):
    log_filename = f"log_{log_data['timestamp']}.json"
    try:
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=log_filename,
            Body=json.dumps(log_data),  # 로그 데이터를 JSON 형식으로 S3에 저장
            ContentType="application/json"
        )
        print(f"로그 저장 성공: {log_filename}")
    except NoCredentialsError:
        print("AWS 자격 증명 오류")
    except Exception as e:
        print(f"로그 저장 실패: {str(e)}")

# Kafka Consumer로 로그 수신
for message in consumer:
    log_data = message.value
    print(f"수신된 로그: {log_data}")
    save_log_to_s3(log_data)
