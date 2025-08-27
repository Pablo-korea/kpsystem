#!/usr/bin/env python3
"""
KP시스템 차트 생성기 API 테스트 스크립트
"""

import requests
import json
from datetime import datetime

def test_api():
    """API 테스트 함수"""
    
    # API 엔드포인트
    base_url = "http://localhost:5000"
    
    # 테스트 데이터
    test_data = {
        "name": "테스트 사용자",
        "birth_date": "1990-01-01T12:00:00",
        "timezone": "Asia/Seoul",
        "latitude": 37.5665,
        "longitude": 126.9780,
        "ayanamsa": "LAHIRI",
        "house_system": "P"
    }
    
    print("=== KP시스템 차트 생성기 API 테스트 ===")
    print(f"서버 URL: {base_url}")
    print(f"테스트 데이터: {json.dumps(test_data, indent=2, ensure_ascii=False)}")
    print()
    
    try:
        # 1. 시간대 목록 API 테스트
        print("1. 시간대 목록 API 테스트...")
        response = requests.get(f"{base_url}/api/timezones")
        if response.status_code == 200:
            timezones = response.json()
            print(f"✅ 성공: {len(timezones)}개의 시간대 반환")
            for tz in timezones[:3]:  # 처음 3개만 출력
                print(f"   - {tz['label']}")
        else:
            print(f"❌ 실패: {response.status_code}")
        print()
        
        # 2. 차트 생성 API 테스트
        print("2. 차트 생성 API 테스트...")
        response = requests.post(
            f"{base_url}/api/chart",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 성공: 차트 생성 완료")
            print(f"   - 이름: {result['metadata']['birth_date']}")
            print(f"   - 시간대: {result['metadata']['timezone']}")
            print(f"   - 아야남샤: {result['metadata']['ayanamsa']}")
            print(f"   - 하우스 시스템: {result['metadata']['house_system']}")
            print()
            
            print("하우스 컵스 결과:")
            for house in result['houses']:
                print(f"   {house['house']:2d}번: {house['dms']} ({house['sign']})")
        else:
            print(f"❌ 실패: {response.status_code}")
            print(f"   오류: {response.text}")
        print()
        
        # 3. 웹 페이지 접근 테스트
        print("3. 웹 페이지 접근 테스트...")
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            print("✅ 성공: 메인 페이지 접근 가능")
        else:
            print(f"❌ 실패: {response.status_code}")
        print()
        
    except requests.exceptions.ConnectionError:
        print("❌ 연결 실패: 서버가 실행되지 않았거나 포트 5000에서 실행되지 않습니다.")
        print("   다음 명령어로 서버를 시작하세요:")
        print("   python app.py")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    test_api() 