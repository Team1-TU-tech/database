#!/bin/bash

# 백그라운드에서 Kafka 컨슈머 실행
python /code/src/database/routers/consumer.py &

# FastAPI 애플리케이션 실행
uvicorn src.database.main:app --host 0.0.0.0 --port 7777

