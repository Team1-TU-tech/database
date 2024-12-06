import os
import pytest
from database.routers.log_handler import log_event

# 고정된 로그 파일 경로
log_filename = "/Users/seon-u/TU-tech/database/logs/api_logs.log"

def test_log_event():
    # 기존에 있던 로그 파일 삭제 (테스트마다 깨끗하게 시작)
    if os.path.exists(log_filename):
        os.remove(log_filename)
    
    # 로그 기록 함수 호출
    user_id = "test_user"
    device = "web"
    action = "Search"
    keyword = "concert"
    category = "music"
    region = "Seoul"
    start_date = "2023-01-01"
    end_date = "2023-12-31"
    num_results = 5
    
    # 로그 이벤트를 기록
    log_event(user_id, device, action, keyword=keyword, category=category, region=region, start_date=start_date, end_date=end_date, num_results=num_results)
    
    # 로그 파일이 실제로 생성되었는지 확인
    assert os.path.exists(log_filename)  # 파일이 존재하는지 확인
    # 파일 읽기
    with open(log_filename, "r") as f:
        logs = f.readlines()
    
    # 로그 파일 내용이 비어있지 않음을 확인
    assert len(logs) > 0
    assert any(f"User: {user_id}" in log for log in logs)
    assert any(f"Device: {device}" in log for log in logs)
    assert any(f"Action: {action}" in log for log in logs)
    assert any(f"keyword: {keyword}" in log for log in logs)
    assert any(f"category: {category}" in log for log in logs)
    assert any(f"region: {region}" in log for log in logs)
    assert any(f"start_date: {start_date}" in log for log in logs)
    assert any(f"end_date: {end_date}" in log for log in logs)
    assert any(f"num_results: {num_results}" in log for log in logs)
    
    # 테스트 후 로그 파일 삭제 (테스트 후 정리)
    os.remove(log_filename)
