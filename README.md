# API
## 개요
- docker-compose를 활용하여 FastAPI 실행, 공연 정보 제공 
- 사용자가 다양한 공연에 대한 정보를 검색, 조회, 추천할 수 있도록 지원
- 사용자 경험을 향상시키기 위해 실시간 로그 데이터 분석 및 머신러닝 기반 추천 기능 제공
<br></br>
## 목차
- [기술스택](#기술스택)
- [개발기간](#개발기간)
- [API](#API)
- [실행요구사항](#실행요구사항)
- [Contributors](#Contributors)
- [License](#License)
- [문의](#문의)
  
<br></br>
## 기술스택
<img src="https://img.shields.io/badge/FastAPI-009688?style=flat&logo=FastAPI&logoColor=FFFFFF"/> <img src="https://img.shields.io/badge/Python-3.11-3776AB?style=flat&logo=Python&logoColor=F5F7F8"/> <img src="https://img.shields.io/badge/MongoDB-47A248?style=flat&logo=MongoDB&logoColor=ffffff"/> <img src="https://img.shields.io/badge/Amazon%20S3-569A31?style=flat&logo=Amazon%20S3&logoColor=ffffff"/>
<br></br>
## 개발기간
`2024.11.28 ~ 2024.12.17(20일)`
<br></br>
## API 

![image](https://github.com/user-attachments/assets/7dc0defc-7f81-4b30-9a73-69b89a23400b)

### search
- 공연 제목, 카테고리, 날짜, 아티스트 이름, 지역으로 공연 정보 검색
### detail
- MongoDB에 저장된 공연 정보를 `id` 기준으로 조회
### banner
- 현재 날짜를 제외한 가장 가까운 공연 11개를 추출하여 메인 화면 배너에 표시
### top_show
- 로그 데이터를 분석하여 가장 많이 클릭된 공연 상위 8개를 추출
### this_weekend
- 현재 날짜를 기준으로 이번 주말에 볼 수 있는 공연 추출
### recommendation
- ML 모델을 활용하여 description 분석 후 `id`에 해당하는 공연과 유사도가 가장 높은 3개 공연 추출 
<br></br>
## 실행 요구 사항 
```bash
# 도커 빌드
docker compose build

# 도커 백그라운드 실행
docker compose up -d
```
### FastAPI 접속
[localhost:7777](https://localhost:7777)
## Contributors
`hahahellooo`, `hamsunwoo`, `oddsummer56`
<br></br>
## License
이 애플리케이션은 TU-tech 라이선스에 따라 라이선스가 부과됩니다.
<br></br>
## 문의
질문이나 제안사항이 있으면 언제든지 연락주세요:
<br></br>
- 이메일: TU-tech@tu-tech.com
- Github: `Mingk42`, `hahahellooo`, `hamsunwoo`, `oddsummer56`
