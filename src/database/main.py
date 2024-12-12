from fastapi import FastAPI
from src.database.routers import tickets, banner, weekend, rank  # tickets 라우터를 포함한 모듈
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000/"],
    allow_credentials=True,
    allow_methods=[""],
    allow_headers=[""],
)

# 라우터를 메인 앱에 연결
app.include_router(tickets.router)
app.include_router(banner.router)
app.include_router(rank.router)
app.include_router(weekend.router)
