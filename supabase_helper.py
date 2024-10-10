from supabase import create_client, Client

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
def add_event_to_supabase(date, value, btn_color, supabase_client: Client):
    """Supabase에 새로운 일정을 추가"""
    data = {"schedule_day": date, "schedule_value": value, "btn_color": btn_color}
    supabase_client.table('minsik_calender').insert(data).execute()
    print("일정이 성공적으로 등록되었습니다.")

def upsert_event_to_supabase(date, value, btn_color, supabase_client: Client):
    """Supabase에서 해당 날짜에 일정을 추가하거나 업데이트하는 함수"""
    data = {
        "schedule_day": date,
        "schedule_value": value,
        "btn_color": btn_color if btn_color else None  # 선택된 색상이 없으면 None
    }
    
    # Upsert를 사용하여 일정 삽입 또는 업데이트
    supabase_client.table('minsik_calender').upsert(data, on_conflict=["schedule_day"]).execute()

    print(f"일정이 성공적으로 추가되었거나 업데이트되었습니다: {date}")

def get_event_by_date(date, supabase_client: Client):
    """Supabase에서 특정 날짜에 해당하는 일정을 가져오는 함수"""
    try:
        response = supabase_client.table('minsik_calender').select('*').eq('schedule_day', date).execute()
        if response.data:
            return response.data[0]  # 해당 날짜의 이벤트가 있다면 반환
        return None  # 해당 날짜에 이벤트가 없을 경우
    except Exception as e:
        print(f"일정을 가져오는 중 오류가 발생: {e}")
        return None


# 특정 날짜에 해당하는 일정 조회 함수
def get_calendar_data_by_date(supabase_client: Client, date: str):
    """선택된 날짜에 해당하는 일정을 조회"""
    response = supabase_client.table('minsik_calender').select('*').eq('schedule_day', date).execute()
    
    return response.data

# 사용자 인증 함수
def verify_login(username, password, supabase_client):
    """Supabase에서 사용자 이름과 비밀번호를 확인하는 함수"""
    try:
        response = supabase_client.table('global_setting').select('*').eq('user_name', username).execute()
        if response.data:  # 데이터가 있을 경우
            user_data = response.data[0]
            return user_data.get('password') == password  # 비밀번호 일치 여부 확인
        else:
            print("사용자 이름을 찾을 수 없습니다.")
            return False
    except Exception as e:
        print(f"로그인 중 오류 발생: {e}")
        return False
    
def get_global_setting(username, supabase_client):
    """Supabase에서 username으로 글로벌 설정을 가져오는 함수"""
    try:
        response = supabase_client.table('global_setting').select('*').eq('user_name', username).execute()
        if response.data:  # 데이터가 있을 경우
            global_color = response.data[0].get('global_color', None)
            if global_color:
                return global_color  # 글로벌 색상 반환
            else:
                return None  # 글로벌 색상이 없으면 None 반환
        else:
            print("사용자 정보에 해당하는 글로벌 세팅값을 찾을 수 없습니다.")
            return None
    except Exception as e:
        print(f"글로벌 세팅값을 가져오는데 오류가 발생: {e}")
        return None

def save_global_color(username, color_value, supabase_client):
    """Supabase에 글로벌 색상을 저장하는 함수"""
    try:
        # 업데이트 요청을 보냄
        response = supabase_client.table('global_setting').update({'global_color': color_value}).eq('user_name', username).execute()

        if response.data:  # response.data가 있으면 성공
            print(f"Supabase 저장 성공: {response.data}")
            return True  # 성공적으로 업데이트
        else:
            print(f"Supabase 저장 실패: {response}")
            return False
    except Exception as e:
        print(f"Supabase에 글로벌 색상 저장 중 오류 발생: {e}")
        return False
    
# 특정 날짜 로컬 색상 초기화
def clear_color_for_date(date: str, supabase_client: Client):
    """주어진 날짜의 btn_color를 null로 설정하는 함수"""
    try:
        response = supabase_client.table('minsik_calender').update({'btn_color': None}).eq('schedule_day', date).execute()
        if response.data:
            return True
        else:
            return False
    except Exception as e:
        print(f"btn_color 초기화 중 오류 발생: {e}")
        return False
    
# 특정 날짜 row가 Empty, Null 상태일 때 해당 row 삭제
def delete_empty_rows_for_date(formatted_date, supabase_client):
    """해당 날짜의 schedule_value와 btn_color가 Empty 또는 Null일 때 해당 행 삭제"""
    print(f"삭제 조건: 날짜 = {formatted_date}")

    # 삭제할 데이터를 가져오기
    existing_event = get_event_by_date(formatted_date, supabase_client)
    
    if existing_event:
        print(f"삭제할 행 - schedule_value: {existing_event.get('schedule_value')}, btn_color: {existing_event.get('btn_color')}")


    response = supabase_client.table('minsik_calender').delete().match({
        'schedule_day': formatted_date,  # 해당 날짜에 맞는 행을 찾아야 합니다.
    }).or_('schedule_value.is.null, schedule_value.eq."", btn_color.is.null, btn_color.eq.""').execute()

    if response.data:  # 삭제가 성공적이면 data는 비어있지 않음
        print(f"{formatted_date}의 빈 행이 성공적으로 삭제되었습니다.")
        return True
    else:
        print(f"{formatted_date}의 행이 존재하지 않아 삭제할 수 없습니다.")
        return False