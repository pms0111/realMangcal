from supabase import create_client, Client
from datetime import datetime

# Supabase URL과 키 설정
supabase_url = "https://ioursknulljozaqqcxvg.supabase.co"
supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlvdXJza251bGxqb3phcXFjeHZnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MjcxNjcxNDcsImV4cCI6MjA0Mjc0MzE0N30.yRZ3Rv5VCEru0WPDvnttW3zKQZ24WqUdh5GRJa548ac"

# Supabase 클라이언트 생성 함수
def create_supabase_client() -> Client:
    """Supabase 클라이언트를 생성하여 반환"""
    return create_client(supabase_url, supabase_key)

# 데이터 조회 함수
def get_calendar_data(supabase_client: Client):
    """Supabase에서 일정을 조회"""
    response = supabase_client.table('minsik_calender').select('*').execute()
    return response.data

# 일정 추가 함수
def add_event_to_supabase(selected_date, value, color, supabase_client: Client):
    # 선택된 날짜를 ISO 형식의 문자열로 변환
    formatted_date = selected_date.isoformat()  # 'YYYY-MM-DDTHH:MM:SS'

    # 기존 데이터 검색
    existing_event = supabase_client.table('minsik_calender').select('*').eq('schedule_day', formatted_date).execute()
    

    """Supabase에 새로운 일정을 추가"""
    data = {
        "schedule_day": formatted_date,
        "schedule_value": value, 
        "btn_color": color
    }

     # 기존 데이터가 있을 경우 업데이트, 없을 경우 삽입
    if existing_event.data:
        # 기존 데이터가 있을 경우 업데이트
        response = supabase_client.table('minsik_calender').update(data).eq('schedule_day', formatted_date).execute()
    else:
        # 기존 데이터가 없을 경우 삽입
        response = supabase_client.table('minsik_calender').insert(data).execute()

    return response  # 성공 여부를 반환하거나 필요한 데이터를 반환하도록 수정할 수 있습니다.

    
    print("일정이 성공적으로 등록되었습니다.")

    # 특정 날짜에 해당하는 일정 조회 함수
def get_calendar_data_by_date(supabase_client: Client, date: str):
    """선택된 날짜에 해당하는 일정을 조회"""
    response = supabase_client.table('minsik_calender').select('*').eq('schedule_day', date).execute()
    
    return response.data

