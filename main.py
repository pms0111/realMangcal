from datetime import datetime, timedelta
import kivy
from kivy.config import Config
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from supabase import create_client, Client
import logging



# Kivy 로그 레벨 설정 (WARNING 이상만 출력되게 설정)
Config.set('kivy', 'log_level', 'warning')

class MyApp(App):
    def build(self):
        # 전체 레이아웃을 그리드로 설정 (캘린더 구조 7열 8행: 월/연도, 요일, 날짜)
        layout = GridLayout(cols=7, rows=8, spacing=5, padding=10)
        
        # 현재 월 및 연도 정보
        current_date = datetime.now()
        month = current_date.month
        year = current_date.year
        
        # 월/연도 레이블 추가
        header = Label(text=f"{year}년 {month}월", size_hint=(1, None), height=40)
        layout.add_widget(header)
        
        # 요일 헤더 추가
        days_of_week = ['일', '월', '화', '수', '목', '금', '토']
        for day in days_of_week:
            layout.add_widget(Label(text=day))
        
        # 달의 첫째 날과 마지막 날 계산
        first_day_of_month = datetime(year, month, 1)
        last_day_of_month = (first_day_of_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        # 첫째 날이 무슨 요일인지 계산하여 공백 추가
        first_day_weekday = first_day_of_month.weekday()  # 월요일이 0, 일요일이 6
        for _ in range((first_day_weekday + 1) % 7):
            layout.add_widget(Label(text=''))
        
        # 날짜 버튼 추가
        for day in range(1, last_day_of_month.day + 1):
            btn = Button(text=str(day), on_press=self.on_date_press)
            layout.add_widget(btn)
        
        return layout
    
    def on_date_press(self, instance):
        # 사용자가 날짜를 클릭하면 출력되는 이벤트
        print(f"날짜 클릭됨: {instance.text}일")

if __name__ == '__main__':
    # Supabase 클라이언트 설정
    url: str = "https://ioursknulljozaqqcxvg.supabase.co"
    key: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlvdXJza251bGxqb3phcXFjeHZnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MjcxNjcxNDcsImV4cCI6MjA0Mjc0MzE0N30.yRZ3Rv5VCEru0WPDvnttW3zKQZ24WqUdh5GRJa548ac"
    supabase: Client = create_client(url, key)

    # Supabase 데이터 조회 (예시)
    response = supabase.table('minsik_calender').select('*').execute()

    
    # print 문이 터미널에 정상적으로 출력되도록 로그 설정
    logging.basicConfig(level=logging.INFO)
    print("Supabase Response Data: ", response.data)

    MyApp().run()
