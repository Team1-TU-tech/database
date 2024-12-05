from kafka import KafkaProducer
import logging
import os
import json
from datetime import datetime
from logging.handlers import RotatingFileHandler

# 로거 설정
logger = logging.getLogger()
logger.setLevel(logging.INFO)  # 기본 로그 레벨 설정

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_message = {
            "timestamp": datetime.now().isoformat(),
            "level": record.levelname,
            "message": record.getMessage()
        }
        return json.dumps(log_message, ensure_ascii=False)

# Kafka 프로듀서 설정 (전역에서 한 번만 설정)
from dotenv import load_dotenv

# .env 파일을 로드하여 환경 변수를 읽기
load_dotenv()

# Kafka 서버 환경 변수에서 값을 읽음
KAFKA_SERVER = os.getenv("KAFKA_SERVER", "kafka:9092")  # 기본값은 kafka:9092

producer = KafkaProducer(
    bootstrap_servers=KAFKA_SERVER,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# 로그 이벤트 함수 정의
def log_event(user_id: str, device: str, action: str, **kwargs):
    # 로그 메시지 생성
    log_message = {
        "timestamp": datetime.now().isoformat(),
        "user_id": user_id,
        "device": device,
        "action": action,
        **kwargs
    }

    # Kafka에 로그 메시지 전송
    producer.send('logs', log_message)
    producer.flush()
    print("로그 데이터 전송 완료!")
    
    # INFO 로그 기록
    #logger.info(log_message)

# 예시 실행
# log_event(user_id="12345", device="Mozilla/5.0", action="login")