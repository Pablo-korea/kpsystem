from fastapi import FastAPI, Request, Depends, HTTPException, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel
import json
import os
from kp import KPChart
from kp_master_table import get_lords_from_master_table
from typing import Optional, Dict, Any
import secrets

def get_planet_name(planet_code):
    """행성 코드를 한국어 행성명으로 변환"""
    planet_names = {
        # 약어 형태
        'Su': '태양',
        'Mo': '달',
        'Ma': '화성',
        'Me': '수성',
        'Ju': '목성',
        'Ve': '금성',
        'Sa': '토성',
        'Ra': '라후',
        'Ke': '케투',
        # 전체 이름 형태
        'sun': '태양',
        'moon': '달',
        'mercury': '수성',
        'venus': '금성',
        'mars': '화성',
        'jupiter': '목성',
        'saturn': '토성',
        'rahu': '라후',
        'ketu': '케투'
    }
    return planet_names.get(planet_code, planet_code)

app = FastAPI(title="KP Astrology System", version="1.0.0")

# 세션 미들웨어 추가
app.add_middleware(SessionMiddleware, secret_key="your-secret-key-here")

# 템플릿 설정
templates = Jinja2Templates(directory="templates")

# 정적 파일 설정 (CSS, JS 등)
# app.mount("/static", StaticFiles(directory="static"), name="static")

def get_house_meaning(house_num):
    """하우스별 의미를 반환하는 함수"""
    meanings = {
        1: "자아, 외모, 성격, 첫인상",
        2: "재물, 가족, 말, 음식, 가치관",
        3: "형제자매, 용기, 의사소통, 단거리 여행",
        4: "어머니, 집, 부동산, 교육, 내적 평화",
        5: "자녀, 창조성, 로맨스, 투기, 지능",
        6: "질병, 적, 서비스, 일상 업무, 애완동물",
        7: "배우자, 파트너십, 결혼, 공개적 적",
        8: "죽음, 변화, 신비, 타인의 재물, 수명",
        9: "종교, 철학, 장거리 여행, 아버지, 운",
        10: "직업, 명성, 사회적 지위, 정부",
        11: "친구, 수입, 희망, 꿈, 사회적 네트워크",
        12: "손실, 지출, 외국, 영성, 해탈, 은둔"
    }
    return meanings.get(house_num, f"{house_num}하우스")

# 템플릿 글로벌 함수 등록
templates.env.globals["get_house_meaning"] = get_house_meaning

# 파일 경로
MEMBERS_FILE = 'members.json'
USERS_FILE = 'users.json'

# Pydantic 모델
class UserLogin(BaseModel):
    username: str
    password: str

class UserRegister(BaseModel):
    username: str
    password: str
    confirm_password: str
    name: str
    email: str

class ChartData(BaseModel):
    member_id: str
    chart_name: str
    birth_date: Optional[str] = ""
    timezone: Optional[str] = "Asia/Seoul"
    latitude: Optional[float] = 37.38
    longitude: Optional[float] = 127.1188
    house_system: Optional[str] = "P"
    ayanamsa: Optional[str] = "LAHIRI"
    house_angles: Optional[Dict[str, str]] = {}
    planet_angles: Optional[Dict[str, str]] = {}
    house_planets: Optional[Dict[str, str]] = {}

def load_members():
    """모든 사용자의 회원 데이터를 로드합니다."""
    if os.path.exists(MEMBERS_FILE):
        with open(MEMBERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_members(members_data):
    """모든 사용자의 회원 데이터를 저장합니다."""
    try:
        print(f"[DEBUG] JSON 파일 저장 시작: {MEMBERS_FILE}")
        with open(MEMBERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(members_data, f, ensure_ascii=False, indent=4)
        print(f"[DEBUG] JSON 파일 저장 완료")
    except Exception as e:
        print(f"[ERROR] JSON 파일 저장 실패: {e}")
        raise

def get_user_members(username):
    """특정 사용자의 회원 데이터만 반환합니다."""
    all_members = load_members()
    return all_members.get(username, {})

def save_user_member(username, member_id, member_data):
    """특정 사용자의 회원 데이터를 저장합니다."""
    try:
        print(f"[DEBUG] save_user_member 시작 - 사용자: {username}, 회원ID: {member_id}")
        all_members = load_members()
        print(f"[DEBUG] 전체 데이터 로드 완료. 기존 사용자: {list(all_members.keys())}")
        
        if username not in all_members:
            all_members[username] = {}
            print(f"[DEBUG] 새 사용자 {username} 추가됨")
        
        all_members[username][member_id] = member_data
        print(f"[DEBUG] 사용자 {username}의 데이터 업데이트 완료. 회원 수: {len(all_members[username])}")
        
        save_members(all_members)
        print(f"[DEBUG] save_user_member 완료")
    except Exception as e:
        print(f"[ERROR] save_user_member 실패: {e}")
        raise

def load_users():
    """사용자 데이터를 로드합니다."""
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            users_data = json.load(f)
            # users 배열을 딕셔너리로 변환
            users_dict = {}
            for user in users_data.get('users', []):
                users_dict[user['username']] = user
            return users_dict
    return {}

def save_users(users_dict):
    """사용자 데이터를 저장합니다."""
    users_list = list(users_dict.values())
    users_data = {"users": users_list}
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users_data, f, ensure_ascii=False, indent=2)

def migrate_existing_data():
    """기존 members.json 데이터를 사용자별 구조로 마이그레이션합니다."""
    if not os.path.exists(MEMBERS_FILE):
        return
    
    try:
        with open(MEMBERS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 데이터가 비어있으면 마이그레이션 불필요
        if not data:
            return
            
        # 올바른 구조인지 확인: {username: {chart_name: chart_data}}
        # 올바른 구조라면 최상위 키는 사용자명이고, 그 하위는 차트명이어야 함
        needs_migration = False
        
        for username, user_data in data.items():
            if not isinstance(user_data, dict):
                needs_migration = True
                break
                
            # user_data의 값들을 확인
            for chart_name, chart_data in user_data.items():
                if isinstance(chart_data, dict):
                    # chart_data에 birth_date가 직접 있다면 올바른 구조
                    if 'birth_date' in chart_data:
                        continue
                    # chart_data가 또 다른 중첩 구조라면 마이그레이션 필요
                    elif any(isinstance(v, dict) and 'birth_date' in str(v) for v in chart_data.values()):
                        needs_migration = True
                        break
        
        if needs_migration:
            print("데이터 구조 마이그레이션이 필요합니다. 수동으로 수정해주세요.")
            
    except Exception as e:
        print(f"데이터 마이그레이션 중 오류: {e}")

def get_current_user(request: Request):
    """현재 로그인한 사용자를 확인합니다."""
    if request.session.get("logged_in") != True:
        # 브라우저 요청인 경우 로그인 페이지로 리다이렉트
        if "text/html" in request.headers.get("accept", ""):
            return None
        else:
            raise HTTPException(status_code=401, detail="로그인이 필요합니다")
    return request.session.get("username")

def login_required(request: Request):
    """로그인이 필요한 엔드포인트를 위한 의존성"""
    return get_current_user(request)

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """로그인 페이지"""
    # 이미 로그인된 경우 메인 페이지로 리다이렉트
    if request.session.get("logged_in"):
        return RedirectResponse(url="/", status_code=302)
    
    flash_data = request.session.pop("flash", None)
    return templates.TemplateResponse("login.html", {
        "request": request,
        "flash": flash_data,
        "session": request.session
    })

@app.post("/login")
async def login(request: Request, username: str = Form(), password: str = Form()):
    """로그인 처리"""
    users = load_users()
    if username in users and users[username]['password'] == password:
        request.session["logged_in"] = True
        request.session["username"] = username
        request.session["user_name"] = users[username].get('name', username)
        request.session["flash"] = {"message": "로그인 성공!", "type": "success"}
        return RedirectResponse(url="/", status_code=302)
    else:
        request.session["flash"] = {"message": "잘못된 사용자명 또는 비밀번호입니다.", "type": "error"}
        return RedirectResponse(url="/login", status_code=302)

@app.get("/logout")
async def logout(request: Request):
    """로그아웃"""
    request.session.clear()
    request.session["flash"] = {"message": "로그아웃되었습니다.", "type": "info"}
    return RedirectResponse(url="/login", status_code=302)

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """회원가입 페이지"""
    flash_data = request.session.pop("flash", None)
    return templates.TemplateResponse("register.html", {
        "request": request,
        "flash": flash_data,
        "session": request.session
    })

@app.post("/register")
async def register(
    request: Request, 
    username: str = Form(), 
    password: str = Form(), 
    confirm_password: str = Form(),
    name: str = Form(), 
    email: str = Form()
):
    """회원가입 처리"""
    # 입력 검증
    if not username or not password or not confirm_password:
        request.session["flash"] = {"message": "사용자명과 비밀번호는 필수입니다.", "type": "error"}
        return RedirectResponse(url="/register", status_code=302)
    
    if password != confirm_password:
        request.session["flash"] = {"message": "비밀번호가 일치하지 않습니다.", "type": "error"}
        return RedirectResponse(url="/register", status_code=302)
    
    if len(password) < 6:
        request.session["flash"] = {"message": "비밀번호는 6자 이상이어야 합니다.", "type": "error"}
        return RedirectResponse(url="/register", status_code=302)
    
    # 기존 사용자 확인
    users = load_users()
    if username in users:
        request.session["flash"] = {"message": "이미 존재하는 사용자명입니다.", "type": "error"}
        return RedirectResponse(url="/register", status_code=302)
    
    # 새 사용자 추가
    new_user = {
        'username': username,
        'password': password,
        'name': name,
        'email': email
    }
    
    users[username] = new_user
    save_users(users)
    
    request.session["flash"] = {"message": "회원가입이 완료되었습니다. 로그인해주세요.", "type": "success"}
    return RedirectResponse(url="/login", status_code=302)

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """메인 페이지"""
    # 로그인 확인
    current_user = get_current_user(request)
    if current_user is None:
        return RedirectResponse(url="/login", status_code=302)
    
    members = get_user_members(current_user)
    flash_data = request.session.pop("flash", None)
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "members": members,
        "flash": flash_data,
        "session": request.session,
        "current_user": current_user
    })

@app.get("/main")
async def main_redirect(request: Request):
    """메인 페이지로 리다이렉트"""
    return RedirectResponse(url="/", status_code=302)

@app.get("/member/{member_id}", response_class=HTMLResponse)
async def member_detail(request: Request, member_id: str, current_user: str = Depends(login_required)):
    """특정 회원의 상세 정보 페이지"""
    members = get_user_members(current_user)
    if member_id not in members:
        raise HTTPException(status_code=404, detail="회원을 찾을 수 없습니다.")
    
    member_data = members[member_id]
    return templates.TemplateResponse("member.html", {
        "request": request,
        "member_id": member_id, 
        "member_data": member_data,
        "session": request.session,
        "current_user": current_user
    })

@app.get("/chart/{chart_name}", response_class=HTMLResponse)
async def chart(request: Request, chart_name: str, current_user: str = Depends(login_required)):
    """차트 페이지"""
    members = get_user_members(current_user)
    if chart_name not in members:
        raise HTTPException(status_code=404, detail="차트를 찾을 수 없습니다.")
    
    chart_data = members[chart_name]
    
    # 기본 변수 초기화
    house_lords = {}
    planet_lords = {}
    significators = {}
    planet_significators = {}
    analysis = {}
    
    # KP 차트 생성
    try:
        print(f"차트 데이터: {chart_data}")
        print(f"birth_date: {chart_data.get('birth_date', 'NOT FOUND')}")
        
        kp_chart = KPChart(
            birth_date=chart_data['birth_date'],
            timezone=chart_data['timezone'],
            latitude=chart_data['latitude'],
            longitude=chart_data['longitude'],
            house_system=chart_data['house_system'],
            ayanamsa=chart_data['ayanamsa']
        )
        
        # 차트 분석
        analysis = kp_chart.analyze_chart()
        
        # 하우스별 마스터 테이블 정보 계산
        house_lords = {}
        for house_num, angle_str in chart_data.get('house_angles', {}).items():
            if angle_str:
                # 각도 문자열에서 도수 추출 (예: "353°03'58\"" 또는 "353º03'58\"" -> 353.066)
                try:
                    # 각도 문자열 파싱 (두 가지 도 기호 모두 처리)
                    angle_str = str(angle_str).replace('"', '').replace("'", ' ')
                    parts = angle_str.replace('°', ' ').replace('º', ' ').split()
                    if len(parts) >= 1:
                        degrees = float(parts[0])
                        minutes = float(parts[1]) if len(parts) > 1 else 0
                        seconds = float(parts[2]) if len(parts) > 2 else 0
                        total_degrees = degrees + minutes/60 + seconds/3600
                        
                        # 마스터 테이블에서 lords 정보 가져오기
                        sign_lord, nakshatra_lord, sub_lord = get_lords_from_master_table(total_degrees)
                        house_lords[house_num] = {
                            'sign_lord': get_planet_name(sign_lord),
                            'nakshatra_lord': get_planet_name(nakshatra_lord),
                            'sub_lord': get_planet_name(sub_lord)
                        }
                except Exception as e:
                    print(f"각도 파싱 오류 (House {house_num}): {e}")
                    house_lords[house_num] = {
                        'sign_lord': '-',
                        'nakshatra_lord': '-',
                        'sub_lord': '-'
                    }
        
        # 행성별 마스터 테이블 정보 계산
        planet_lords = {}
        for planet_code, angle_str in chart_data.get('planet_angles', {}).items():
            if angle_str:
                # 각도 문자열에서 도수 추출
                try:
                    # 각도 문자열 파싱 (두 가지 도 기호 모두 처리)
                    angle_str = str(angle_str).replace('"', '').replace("'", ' ')
                    parts = angle_str.replace('°', ' ').replace('º', ' ').split()
                    if len(parts) >= 1:
                        degrees = float(parts[0])
                        minutes = float(parts[1]) if len(parts) > 1 else 0
                        seconds = float(parts[2]) if len(parts) > 2 else 0
                        total_degrees = degrees + minutes/60 + seconds/3600
                        
                        # 마스터 테이블에서 lords 정보 가져오기
                        sign_lord, nakshatra_lord, sub_lord = get_lords_from_master_table(total_degrees)
                        planet_lords[planet_code] = {
                            'sign_lord': get_planet_name(sign_lord),
                            'nakshatra_lord': get_planet_name(nakshatra_lord),
                            'sub_lord': get_planet_name(sub_lord)
                        }
                except Exception as e:
                    print(f"각도 파싱 오류 (Planet {planet_code}): {e}")
                    planet_lords[planet_code] = {
                        'sign_lord': '-',
                        'nakshatra_lord': '-',
                        'sub_lord': '-'
                    }
        
        print("=== 디버깅 정보 ===")
        print(f"house_lords: {house_lords}")
        print(f"planet_lords: {planet_lords}")
        
        # KP 시그니피케이터 계산
        significators = {}
        
        # 행성명을 코드로 변환하는 매핑
        planet_name_to_code = {
            '태양': 'sun', '달': 'moon', '수성': 'mercury', '금성': 'venus', 
            '화성': 'mars', '목성': 'jupiter', '토성': 'saturn', '라후': 'rahu', '케투': 'ketu'
        }
        
        for house_num in range(1, 13):
            house_str = str(house_num)
            
            # A: 하우스의 사인로드
            A = house_lords.get(house_str, {}).get('sign_lord', '-')
            print(f"House {house_num}: A (사인로드) = {A}")
            print(f"  house_lords[{house_str}] = {house_lords.get(house_str, {})}")
            
            # B: 행성각도에서 그 사인로드가 낙샤트라로드에 있는 행성들
            B_planets = []
            if A != '-':
                print(f"  A가 {A}이므로, 이 행성이 낙샤트라로드에 있는 행성들을 찾는 중...")
                for planet_code, lords in planet_lords.items():
                    nakshatra_lord = lords.get('nakshatra_lord')
                    print(f"    {planet_code}의 낙샤트라로드: {nakshatra_lord}")
                    if nakshatra_lord == A:
                        planet_korean = {
                            'sun': '태양', 'moon': '달', 'mercury': '수성', 'venus': '금성',
                            'mars': '화성', 'jupiter': '목성', 'saturn': '토성', 
                            'rahu': '라후', 'ketu': '케투'
                        }.get(planet_code, planet_code)
                        B_planets.append(planet_korean)
                        print(f"    -> {planet_korean} 추가됨")
            else:
                print(f"  A가 '-'이므로 B를 계산할 수 없음")
            B = ', '.join(B_planets) if B_planets else '-'
            print(f"  B = {B}")
            
            # C: 그 하우스에 있는 행성들
            C = chart_data.get('house_planets', {}).get(house_str, '-')
            if not C or C.strip() == '':
                C = '-'
            
            # D: C의 행성들이 낙샤트라로드인 행성들을 행성각도표에서 찾기
            D_planets = []
            if C != '-':
                # C의 행성들을 파싱
                c_planet_names = [p.strip() for p in C.split(',') if p.strip()]
                for c_planet in c_planet_names:
                    print(f"    C의 행성: {c_planet}")
                    
                    # 이 C 행성이 낙샤트라로드인 행성들을 행성각도표에서 찾기
                    for planet_code, lords in planet_lords.items():
                        if lords.get('nakshatra_lord') == c_planet:
                            planet_korean = get_planet_name(planet_code)
                            if planet_korean not in D_planets:
                                D_planets.append(planet_korean)
                                print(f"      -> {planet_korean} 추가됨 ({c_planet}이 낙샤트라로드)")
            D = ', '.join(D_planets) if D_planets else '-'
            
            significators[house_num] = {
                'A': A,
                'B': B,
                'C': C,
                'D': D
            }
        
        # 행성 시그니피케이터 데이터 (임시 데이터)
        planet_significators = {}
        planets = ['sun', 'moon', 'mercury', 'venus', 'mars', 'jupiter', 'saturn', 'rahu', 'ketu']
        for planet in planets:
            planet_significators[planet] = {
                'A': '-',
                'B': '-',
                'C': '-', 
                'D': '-'
            }
        
        # KP 행성 시그니피케이터 계산
        planet_significators = {}
        
        # 모든 행성에 대해 시그니피케이터 계산
        planets = ['sun', 'moon', 'mercury', 'venus', 'mars', 'jupiter', 'saturn', 'rahu', 'ketu']
        
        for planet in planets:
            planet_korean = get_planet_name(planet)
            planet_significators[planet_korean] = {'A': [], 'B': [], 'C': [], 'D': []}
            
            # 각 하우스의 시그니피케이터를 확인
            for house_num in range(1, 13):
                house_sig = significators.get(house_num, {})
                
                # A: 이 행성이 하우스의 A(사인로드)에 있는가?
                if house_sig.get('A') == planet_korean:
                    planet_significators[planet_korean]['A'].append(house_num)
                
                # B: 이 행성이 하우스의 B에 있는가?
                b_planets = house_sig.get('B', '-').split(', ') if house_sig.get('B') != '-' else []
                if planet_korean in b_planets:
                    planet_significators[planet_korean]['B'].append(house_num)
                
                # C: 이 행성이 하우스의 C에 있는가?
                c_planets = house_sig.get('C', '-').split(', ') if house_sig.get('C') != '-' else []
                if planet_korean in c_planets:
                    planet_significators[planet_korean]['C'].append(house_num)
                
                # D: 이 행성이 하우스의 D에 있는가?
                d_planets = house_sig.get('D', '-').split(', ') if house_sig.get('D') != '-' else []
                if planet_korean in d_planets:
                    planet_significators[planet_korean]['D'].append(house_num)

        print(f"=== 행성 시그니피케이터 디버깅 ===")
        print(f"significators: {significators}")
        print(f"planet_significators: {planet_significators}")
        
        return templates.TemplateResponse("chart.html", {
            "request": request,
            "chart_name": chart_name,
            "chart_data": chart_data,
            "analysis": analysis,
            "significators": significators,
            "planet_significators": planet_significators,
            "house_lords": house_lords,
            "planet_lords": planet_lords,
            "session": request.session,
            "current_user": current_user
        })
    except Exception as e:
        import traceback
        print("=== 차트 생성 오류 ===")
        print(f"오류: {str(e)}")
        print(f"트레이스백: {traceback.format_exc()}")
        
        # 오류 발생 시에도 기본 템플릿을 반환 (빈 데이터로)
        return templates.TemplateResponse("chart.html", {
            "request": request,
            "chart_name": chart_name,
            "chart_data": chart_data,
            "analysis": analysis,
                         "significators": significators,
             "planet_significators": planet_significators,
             "house_lords": house_lords,
             "planet_lords": planet_lords,
             "session": request.session,
             "current_user": current_user,
             "error_message": f"차트 생성 중 오류가 발생했습니다: {str(e)}"
         })

@app.post("/generate_chart")
async def generate_chart(request: Request, current_user: str = Depends(login_required)):
    """차트 생성 API"""
    try:
        # JSON 또는 폼 데이터 받기
        if request.headers.get("content-type", "").startswith("application/json"):
            data = await request.json()
        else:
            form_data = await request.form()
            data = dict(form_data)
        
        print(f"[DEBUG] 받은 데이터: {data}")
        
        # 필수 데이터 검증
        required_fields = ['member_id', 'chart_name']
        for field in required_fields:
            if field not in data or not data[field]:
                print(f"[ERROR] 필수 필드 누락: {field}")
                return JSONResponse(
                    status_code=400,
                    content={'error': f'{field}는 필수입니다.'}
                )
        
        member_id = data['member_id']
        chart_name = data['chart_name']
        
        print(f"[DEBUG] 처리할 데이터 - member_id: {member_id}, chart_name: {chart_name}")
        
        # 차트명 유효성 검사
        if not chart_name.strip():
            print(f"[ERROR] 빈 차트명")
            return JSONResponse(
                status_code=400,
                content={'error': '차트명은 필수입니다.'}
            )
        
        # 하우스 각도 데이터 수집
        house_angles = {}
        for i in range(1, 13):
            house_key = f'house_{i}_angle'  # _angle 추가
            if house_key in data and data[house_key]:
                house_angles[str(i)] = data[house_key]
        
        # 행성 각도 데이터 수집
        planet_angles = {}
        planets = ['sun', 'moon', 'mercury', 'venus', 'mars', 'jupiter', 'saturn', 'rahu', 'ketu']
        for planet in planets:
            planet_key = f'{planet}_angle'  # _angle 추가
            if planet_key in data and data[planet_key]:
                planet_angles[planet] = data[planet_key]
        
        # 하우스별 행성 데이터 수집
        house_planets = {}
        for i in range(1, 13):
            planet_key = f'house_{i}_planets'
            if planet_key in data:
                house_planets[str(i)] = data[planet_key]
            else:
                house_planets[str(i)] = ""
        
        # 차트 데이터 구성
        print(f"[DEBUG] 차트 데이터 구성 시작")
        print(f"[DEBUG] house_angles: {house_angles}")
        print(f"[DEBUG] planet_angles: {planet_angles}")
        print(f"[DEBUG] house_planets: {house_planets}")
        
        chart_data = {
            'name': chart_name,
            'birth_date': data.get('birth_date', ''),
            'timezone': data.get('timezone', 'Asia/Seoul'),
            'latitude': float(data.get('latitude', 37.38)) if data.get('latitude') else 37.38,
            'longitude': float(data.get('longitude', 127.1188)) if data.get('longitude') else 127.1188,
            'house_system': data.get('house_system', 'P'),
            'ayanamsa': data.get('ayanamsa', 'LAHIRI'),
            'house_angles': house_angles,
            'planet_angles': planet_angles,
            'house_planets': house_planets
        }
        
        print(f"[DEBUG] 최종 차트 데이터: {chart_data}")
        
        # 기존 데이터 확인 및 저장
        try:
            print(f"[DEBUG] 데이터 저장 시작 - 사용자: {current_user}, 차트명: {chart_name}")
            user_members = get_user_members(current_user)
            print(f"[DEBUG] 기존 사용자 데이터 로드 완료: {list(user_members.keys())}")
            
            # 기존에 동일한 이름의 차트가 있는지 확인
            is_update = chart_name in user_members
            print(f"[DEBUG] 업데이트 여부: {is_update}")
            
            # 데이터 저장 (기존 데이터 업데이트 또는 신규 추가)
            print(f"[DEBUG] 차트 데이터 저장 시작...")
            save_user_member(current_user, chart_name, chart_data)
            print(f"[DEBUG] 차트 데이터 저장 완료")
            
            # 성공 메시지 구성
            if is_update:
                message = f'"{chart_name}" 차트가 성공적으로 업데이트되었습니다.'
            else:
                message = f'"{chart_name}" 차트가 성공적으로 생성되었습니다.'
                
        except Exception as save_error:
            print(f"[ERROR] 데이터 저장 중 오류: {save_error}")
            return JSONResponse(
                status_code=500,
                content={'error': f'데이터 저장 중 오류가 발생했습니다: {str(save_error)}'}
            )
        
        return JSONResponse(content={
            'success': True,
            'message': message,
            'redirect_url': f'/chart/{chart_name}',
            'is_update': is_update
        })
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={'error': f'차트 생성 중 오류가 발생했습니다: {str(e)}'}
        )

@app.get("/about", response_class=HTMLResponse)
async def about(request: Request, current_user: str = Depends(login_required)):
    """소개 페이지"""
    return templates.TemplateResponse("about.html", {
        "request": request,
        "session": request.session,
        "current_user": current_user
    })

@app.get("/api/members")
async def api_members(current_user: str = Depends(login_required)):
    """API: 현재 사용자의 모든 회원 데이터 반환"""
    members = get_user_members(current_user)
    print(f"사용자 {current_user}의 회원 데이터: {members}")
    return members

@app.get("/api/member/{member_id}")
async def api_member(member_id: str, current_user: str = Depends(login_required)):
    """API: 현재 사용자의 특정 회원 데이터 반환"""
    members = get_user_members(current_user)
    print(f"API 요청: /api/member/{member_id}")
    print(f"사용자: {current_user}")
    print(f"전체 회원 데이터: {members}")
    print(f"요청된 회원 ID: '{member_id}'")
    print(f"사용 가능한 회원 ID들: {list(members.keys())}")
    
    if member_id not in members:
        print(f"회원 '{member_id}'을 찾을 수 없음")
        raise HTTPException(status_code=404, detail="회원을 찾을 수 없습니다.")
    
    member_data = members[member_id]
    print(f"반환할 회원 데이터: {member_data}")
    return member_data

@app.delete("/api/member/{member_id}")
async def api_delete_member(member_id: str, current_user: str = Depends(login_required)):
    """API: 현재 사용자의 특정 회원 데이터 삭제"""
    try:
        print(f"[DEBUG] 데이터 삭제 요청 - 사용자: {current_user}, 회원ID: {member_id}")
        
        # 현재 사용자의 데이터 가져오기
        members = get_user_members(current_user)
        
        if member_id not in members:
            print(f"[ERROR] 회원 '{member_id}'을 찾을 수 없음")
            return JSONResponse(
                status_code=404,
                content={'success': False, 'error': '삭제할 데이터를 찾을 수 없습니다.'}
            )
        
        # 전체 데이터에서 해당 회원 삭제
        all_members = load_members()
        if current_user in all_members and member_id in all_members[current_user]:
            del all_members[current_user][member_id]
            print(f"[DEBUG] 회원 '{member_id}' 삭제 완료")
            
            # 파일에 저장
            save_members(all_members)
            print(f"[DEBUG] 데이터 파일 저장 완료")
            
            return JSONResponse(content={
                'success': True,
                'message': f'"{member_id}" 데이터가 성공적으로 삭제되었습니다.'
            })
        else:
            print(f"[ERROR] 데이터 구조에서 회원을 찾을 수 없음")
            return JSONResponse(
                status_code=404,
                content={'success': False, 'error': '삭제할 데이터를 찾을 수 없습니다.'}
            )
            
    except Exception as e:
        print(f"[ERROR] 데이터 삭제 중 오류: {e}")
        return JSONResponse(
            status_code=500,
            content={'success': False, 'error': f'데이터 삭제 중 오류가 발생했습니다: {str(e)}'}
        )

# 애플리케이션 시작 시 마이그레이션 실행
migrate_existing_data()

if __name__ == '__main__':
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True) 