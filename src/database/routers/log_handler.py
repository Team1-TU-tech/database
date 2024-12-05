import logging
import os
import json
from datetime import datetime

# 로그 파일 경로 설정
log_directory = "/Users/seon-u/TU-tech/database/logs"
log_filename = "api_logs.log"

# 디렉토리가 존재하지 않으면 생성
if not os.path.exists(log_directory):
    os.makedirs(log_directory)

# 로그 파일 경로 설정
log_filepath = os.path.join(log_directory, log_filename)

# 로거 설정
logger = logging.getLogger()
logger.setLevel(logging.INFO)  # 로그 레벨을 INFO로 설정 (INFO, ERROR 등)

# FileHandler를 사용해 파일로 로그 기록
file_handler = logging.FileHandler(log_filepath)
file_handler.setLevel(logging.INFO)  # 파일에 기록할 로그 레벨 설정

# 로그 형식 설정
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)

# 핸들러 추가
logger.addHandler(file_handler)

def log_event(user_id: str, device: str, action: str, **kwargs):
    """
    로그를 기록하는 함수
    :param user_id: 사용자 ID
    :param device: 디바이스 정보
    :param action: 액션 정보 (예: 검색, 상세 조회 등)
    :param kwargs: 추가적인 정보들 (예: 날짜, 키워드 등)
    """
    
    # 로그 메시지 생성
    log_message = {
        "timestamp": datetime.now().isoformat(),
        "user_id": user_id,
        "device": device,
        "action": action,
        **kwargs
    }

    #logger.info(json.dumps(log_message))
    json_message = json.dumps(log_message, ensure_ascii=False)
    # 유니코드 문자열을 그대로 출력
    print("Logging event:", json_message)

    # 로그 기록
    logger.info(json_message)

# 테스트: 로그 기록
log_event("test_user2", "web", "search", category="연극", keyword="아이유") 
