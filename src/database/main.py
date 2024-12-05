from fastapi import FastAPI
from src.database.routers import tickets  # tickets 라우터를 포함한 모듈

app = FastAPI()

# 라우터를 메인 앱에 연결
app.include_router(tickets.router)

