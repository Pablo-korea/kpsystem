# KP시스템 차트 생성기

정확한 천문학적 계산을 통한 Krishnamurti Paddhati (KP) 점성술 차트를 생성하는 웹 애플리케이션입니다.

## 🚀 주요 기능

- **정확한 천문학적 계산**: Astropy 라이브러리를 사용한 정밀한 계산
- **다양한 하우스 시스템**: Placidus 및 Equal House 시스템 지원
- **아야남샤 선택**: 라히리(Lahiri) 및 KP New 아야남샤 지원
- **전 세계 시간대**: 다양한 시간대와 위치 지원
- **사용자 친화적 인터페이스**: 직관적이고 아름다운 웹 인터페이스
- **API 지원**: JSON API를 통한 프로그래밍 방식 접근
- **차트 다운로드**: 생성된 차트를 JSON 형식으로 다운로드

## 📋 시스템 요구사항

- Python 3.8 이상
- pip (Python 패키지 관리자)

## 🛠️ 설치 및 실행

### 1. 저장소 클론
```bash
git clone <repository-url>
cd kpsystem
```

### 2. 가상환경 생성 및 활성화
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. 의존성 설치
```bash
pip install -r requirements.txt
```

### 4. 애플리케이션 실행
```bash
python app.py
```

### 5. 브라우저에서 접속
```
http://localhost:5000
```

## 📖 사용법

### 웹 인터페이스 사용

1. **기본 정보 입력**
   - 이름 입력
   - 생년월일 및 시간 입력
   - 시간대 선택
   - 위도/경도 입력
   - 아야남샤 선택 (라히리 또는 KP New)
   - 하우스 시스템 선택 (Placidus 또는 Equal House)

2. **차트 생성**
   - "차트 생성" 버튼 클릭
   - 결과 확인 및 해석

3. **결과 활용**
   - 차트 인쇄
   - JSON 형식으로 다운로드
   - 새 차트 생성

### API 사용

#### 차트 생성 API
```bash
POST /api/chart
Content-Type: application/json

{
    "name": "홍길동",
    "birth_date": "1990-01-01T12:00:00",
    "timezone": "Asia/Seoul",
    "latitude": 37.5665,
    "longitude": 126.9780,
    "ayanamsa": "LAHIRI",
    "house_system": "P"
}
```

#### 시간대 목록 API
```bash
GET /api/timezones
```

## 🏗️ 프로젝트 구조

```
kpsystem/
├── app.py              # Flask 애플리케이션 메인 파일
├── kp.py               # KP시스템 계산 엔진
├── requirements.txt    # Python 의존성 목록
├── README.md          # 프로젝트 설명서
├── templates/         # HTML 템플릿
│   ├── base.html      # 기본 레이아웃
│   ├── index.html     # 메인 페이지
│   ├── chart.html     # 차트 결과 페이지
│   └── about.html     # 소개 페이지
└── venv/              # 가상환경 (생성됨)
```

## 🔧 기술 스택

- **Backend**: Python, Flask
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **천문학 계산**: Astropy, NumPy
- **시간대 처리**: Pytz
- **폼 처리**: Flask-WTF, WTForms

## 📊 계산 정확도

이 애플리케이션은 다음과 같은 정밀한 천문학적 계산을 수행합니다:

- **Julian Day Number**: 정확한 천문학적 날짜 계산
- **Local Sidereal Time (LST)**: 현지 항성시 계산
- **Obliquity of Ecliptic**: 황도경사각 계산
- **House Cusps**: 하우스 컵스 계산 (Placidus/Equal)
- **Ayanamsa**: 아야남샤 적용

## 🌟 KP시스템 특징

### Krishnamurti Paddhati (KP)
- 인도의 유명한 점성술사 K.S. Krishnamurti가 개발
- 전통적인 베다 점성술 기반
- 정밀하고 실용적인 예측 시스템
- Sub Lords를 통한 세분화된 분석

### 하우스 시스템
- **Placidus**: 가장 널리 사용되는 시스템, 위도에 따른 가변적 하우스 크기
- **Equal House**: Ascendant부터 30도씩 균등 분할

### 아야남샤
- **라히리 (Lahiri)**: 인도 정부 공식 채택, 가장 널리 사용
- **KP New**: KP시스템 전용, 더욱 정밀한 계산

## 📱 주요 도시 좌표

| 도시 | 위도 | 경도 |
|------|------|------|
| 서울 | 37.5665°N | 126.9780°E |
| 도쿄 | 35.6762°N | 139.6503°E |
| 뉴욕 | 40.7128°N | 74.0060°W |
| 런던 | 51.5074°N | 0.1278°W |
| 파리 | 48.8566°N | 2.3522°E |
| 델리 | 28.7041°N | 77.1025°E |

## ⚠️ 면책 조항

이 애플리케이션은 교육 및 연구 목적으로 제공됩니다. 점성술적 해석은 참고용이며, 중요한 인생 결정에는 전문가의 조언을 구하시기 바랍니다.

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 📞 문의

프로젝트에 대한 문의사항이 있으시면 이슈를 생성해 주세요.

---

**KP시스템 차트 생성기** - 정확한 천문학적 계산을 통한 점성술 차트 생성 