import logging
import os
import json
from datetime import datetime, timedelta
from kivy.app import App
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, Line  # Color와 Rectangle 임포트
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.colorpicker import ColorPicker
from kivy.uix.textinput import TextInput
from kivy.uix.modalview import ModalView
from kivy.uix.popup import Popup
from kivy.properties import NumericProperty, ListProperty
from supabase import Client
import supabase_helper
import ast  # 문자열을 tuple로 변환하기 위해 사용

# 로그 설정 (INFO 레벨로 설정)
logging.basicConfig(level=logging.INFO)

LOGIN_FILE = "login_info.json"  # 로그인 정보를 저장할 파일
global_color = [1, 1, 1, 1]  # 기본 값으로 흰색을 설정
Window.clearcolor = (0, 0.125, 0.2, 1) # kivy 전체 백그라운드 색상

class LoginModal(ModalView):
    def __init__(self, calendar_layout, supabase_client, **kwargs):
        super().__init__(**kwargs)
        self.calendar_layout = calendar_layout
        self.supabase_client = supabase_client  # Supabase 클라이언트 저장
        self.size_hint = (0.8, 0.4)
        self.auto_dismiss = False  # 로그인 전에는 닫히지 않도록 설정

        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        self.username_input = TextInput(hint_text='사용자 이름', multiline=False, font_name='NanumGothic.ttf')
        self.password_input = TextInput(hint_text='비밀번호', multiline=False, password=True, font_name='NanumGothic.ttf')

        login_button = Button(text='로그인', on_press=self.login, font_name='NanumGothic.ttf')

        layout.add_widget(Label(text='로그인', font_name='NanumGothic.ttf'))
        layout.add_widget(self.username_input)
        layout.add_widget(self.password_input)
        layout.add_widget(login_button)

        self.add_widget(layout)

    def login(self, instance=None):
        username = self.username_input.text
        password = self.password_input.text

        # 로그인 검증 (supabase_client를 인자로 전달)
        if supabase_helper.verify_login(username, password, self.supabase_client):
            print("로그인 성공")
            self.save_login_info(username)  # 로그인 성공 시 날짜 저장
            self.remove_login_popup()  # 로그인 팝업 닫기
            self.calendar_layout.load_all_events()  # 로그인 성공 후 달력 데이터를 불러옴
        else:
            # 로그인 실패 시 오류 메시지 표시
            print("로그인 실패")
            self.username_input.text = ""
            self.password_input.text = ""
            self.password_input.hint_text = "로그인 실패. 다시 시도하세요."
            

    def save_login_info(self, username):
        """로그인 날짜를 파일에 저장"""
        login_data = {
            "last_login": datetime.now().isoformat(),
            "username": username  # 사용자 이름 저장
        }
        with open(LOGIN_FILE, "w") as f:
            json.dump(login_data, f)

    def remove_login_popup(self):
        """부모 레이아웃에서 ModalView 제거"""
        if self.parent:
            self.parent.remove_widget(self)


class ColorPickerPopup(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.color_picker = ColorPicker()
        self.color_picker.bind(color=self.on_color)  # 색상이 선택될 때 이벤트 바인딩
        self.add_widget(self.color_picker)

    def on_color(self, instance, value):
        # 선택한 색상을 적용할 메서드
        self.parent.parent.update_button_color(value)  # 부모에서 update_button_color 호출

class CalendarLayout(BoxLayout):
    year = NumericProperty(datetime.now().year)
    month = NumericProperty(datetime.now().month)
    day = NumericProperty(datetime.now().day)
    supabase_client: Client = None  # Supabase 클라이언트를 저장할 변수
    events = []  # 전체 일정 데이터를 저장할 리스트
    color_picker_popup = None # 팝업 인스턴스를 저장할 속성 추가
    selected_color = ListProperty([0.7, 0.7, 0.7, 1])  # 선택한 색상 저장, 초기값 설정
    
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.supabase_client = supabase_helper.create_supabase_client()  # Supabase 클라이언트 생성
        # 로그인 팝업 표시 여부 결정
        if self.should_show_login_popup():
            self.show_login_popup()  # 로그인 팝업을 띄우고 달력 로딩은 하지 않음
        else:
            self.load_all_events()  # 로그인 기록이 있으면 바로 달력 데이터를 불러옴
            self.update_calendar()

    def should_show_login_popup(self):
        """로그인 팝업을 띄울지 여부를 판단"""
        if os.path.exists(LOGIN_FILE):
            try:
                with open(LOGIN_FILE, "r") as f:
                    login_data = json.load(f)
                    last_login = datetime.fromisoformat(login_data["last_login"])
                    # 마지막 로그인 날짜로부터 3개월이 지났는지 확인
                    if datetime.now() < last_login + timedelta(days=90):
                        print("3개월 이내에 로그인한 기록이 있습니다.")
                        return False
            except (json.JSONDecodeError, KeyError, ValueError):
                print("로그인 정보 파일이 손상되었거나 비어 있습니다.")
                # 파일이 손상되었거나 비어 있을 경우, 팝업을 띄우고 파일을 다시 저장합니다.
                return True
        print("로그인 팝업을 띄웁니다.")
        return True
    
    def show_login_popup(self):
        """로그인 팝업을 표시하는 함수"""
        self.login_popup = LoginModal(calendar_layout=self, supabase_client=self.supabase_client)
        self.login_popup.open()  # 로그인 팝업을 띄우기

    def parse_color(self, color_string):
        """문자열 형식의 색상 데이터를 tuple로 변환"""
        try:
            return ast.literal_eval(color_string)  # 문자열을 tuple로 변환
        except (ValueError, SyntaxError):
            return (1, 1, 1, 1)  # 변환 실패 시 기본 흰색 반환

    def load_all_events(self):
        """로그인 후 Supabase에서 전체 일정을 불러옴"""
        # 로그인된 사용자 이름 가져오기 (예시로 저장된 사용자 이름 사용)
        username = self.get_logged_in_username()
        logging.info(f"username: {username}")

        # 글로벌 색상 가져오기
        global_color = supabase_helper.get_global_setting(username, self.supabase_client)
        if global_color:
            self.selected_color = self.parse_color(global_color)  # 글로벌 색상 적용
            logging.info(f"글로벌 색상이 적용되었습니다: {self.selected_color}")
        else :
            logging.info(f"username: {username}, global_color가 없습니다")

        # Supabase에서 일정 데이터를 불러옴
        response = supabase_helper.get_calendar_data(self.supabase_client)
        self.events = response  # 전체 일정을 변수에 저장
        logging.info(f"전체 {len(self.events)}개 일정 로드")  # 전체 일정 로드 로그 출력
        self.update_calendar()  # 로그인 후 달력 업데이트

    def get_logged_in_username(self):
        """로그인한 사용자 이름을 가져오는 함수 (저장된 로그인 정보를 사용)"""
        if os.path.exists(LOGIN_FILE):
            try:
                with open(LOGIN_FILE, "r") as f:
                    login_data = json.load(f)
                    return login_data.get("username", None)
            except (json.JSONDecodeError, FileNotFoundError):
                print("로그인 정보 파일이 손상되었거나 비어 있습니다.")
                return None  # 파일이 손상되었으면 그냥 None 반환
        return None


    def refresh_calendar(self):
        """새로고침 버튼을 클릭했을 때 데이터를 다시 불러오고 달력을 갱신하는 메서드"""
        logging.info("데이터 새로고침 중...")
        self.load_all_events()  # 새 데이터를 불러옴
        self.update_calendar()  # 달력을 새로 그리기

    def setGlobalColor(self):
        """글로벌 색상 선택 팝업을 열기 위한 메서드"""
        color_picker = ColorPicker()

        # 색상 선택기에서 색상 변경 시 호출되는 메서드
        color_picker.bind(color=self.on_color)

        # 저장 버튼 생성
        save_button = Button(text="저장", size_hint=(1, 0.2), font_name="NanumGothic.ttf", on_press=self.on_save_color)

        # 팝업 객체 생성
        self.color_popup = ModalView(size_hint=(0.8, 0.8), padding=20)

        # 레이아웃에 ColorPicker와 저장 버튼 추가
        popup_layout = BoxLayout(orientation='vertical', spacing=10)
        popup_layout.add_widget(color_picker)
        popup_layout.add_widget(save_button)

        self.color_popup.add_widget(popup_layout)

        # 팝업 열기
        self.color_popup.open()

    def on_color(self, instance, value):
        """선택된 색상을 모든 버튼에 적용하는 메서드"""
        self.selected_color = value  # 선택한 색상을 저장
        logging.info(f"새로 선택된 글로벌 색상: {self.selected_color}")
        self.update_calendar()  # 색상 선택 후 즉시 업데이트

    def on_save_color(self, instance):
        """선택한 색상을 Supabase에 저장하는 메서드"""
        username = self.get_logged_in_username()  # 로그인된 사용자 이름 가져오기

        if username:
            # Supabase에 글로벌 색상 저장
            color_value = str(self.selected_color)  # 색상 값을 문자열로 변환
            success = supabase_helper.save_global_color(username, color_value, self.supabase_client)

            if success:
                logging.info(f"{username}의 글로벌 색상이 성공적으로 저장되었습니다: {color_value}")
                self.color_popup.dismiss()  # 저장 후 팝업 닫기
                self.update_calendar()  # 색상 업데이트
            else:
                logging.error("글로벌 색상 저장에 실패했습니다.")
        else:
            logging.error("로그인된 사용자가 없습니다.")

    def calculate_brightness(self, color):
        # RGB 색상을 기반으로 밝기를 계산
        r, g, b = color[:3]  # color는 [R, G, B, A] 형식이므로 앞의 세 값을 사용
        brightness = 0.299 * r + 0.587 * g + 0.114 * b
        return brightness


    def get_events_for_month(self, year, month):
        """특정 연도와 월에 해당하는 일정을 필터링"""
        month_start = datetime(year, month, 1)  # 해당 월의 1일
        next_month = (month_start + timedelta(days=32)).replace(day=1)  # 다음 달의 1일
        month_end = next_month - timedelta(days=1)  # 해당 월의 마지막 날

        # 해당 월의 일정만 필터링 (날짜 부분만 비교, 시간은 무시)
        filtered_events = [event for event in self.events if month_start <= datetime.strptime(event['schedule_day'][:10], "%Y-%m-%d") <= month_end]
        logging.info(f"{year}년 {month}월에 대한 {len(filtered_events)}개 일정 필터링")  # 필터링된 일정 로그 출력
        return filtered_events

    def update_calendar(self):
        # 달력을 업데이트하기 전에 글로벌 색상 로그를 남김
        logging.info(f"Updating calendar with global color: {self.selected_color}")
    
        # 수동으로 calendar_grid를 참조 (ids를 통해 kv 파일의 id로 연결)
        calendar_grid = self.ids['calendar_grid']
        calendar_grid.clear_widgets()
        

        # 해당 월의 시작 날짜와 끝 날짜 계산
        first_day_of_month = datetime(self.year, self.month, 1)
        next_month = (first_day_of_month + timedelta(days=32)).replace(day=1)
        last_day_of_month = next_month - timedelta(days=1)

        # 이전 달의 마지막 날짜 계산
        previous_month = first_day_of_month - timedelta(days=1)
        previous_month_last_day = previous_month.day
        first_weekday = (first_day_of_month.weekday() + 1) % 7

        # 현재 월과 이전/다음 달의 일정 필터링
        current_month_events = self.get_events_for_month(self.year, self.month)
        previous_month_events = self.get_events_for_month(self.year if self.month > 1 else self.year - 1, 12 if self.month == 1 else self.month - 1)
        next_month_events = self.get_events_for_month(self.year if self.month < 12 else self.year + 1, 1 if self.month == 12 else self.month + 1)


        # 오늘 날짜 가져오기
        today = datetime.today()
        today_str = today.strftime('%Y-%m-%d')  # YYYY-MM-DD 형식으로 변환


        # 요일 맞추기 위해 이전 달의 날짜와 일정 채우기
        for day in range(first_weekday):
            prev_day = previous_month_last_day - first_weekday + day + 1
            date_str = f"{self.year if self.month > 1 else self.year - 1}-{12 if self.month == 1 else self.month - 1:02}-{prev_day:02}"
            day_events = [event for event in previous_month_events if event['schedule_day'][:10] == date_str]
            # 다음 달 버튼: 글로벌 색상을 기반으로 채도 낮춘 색상 적용
            darker_color = [c * 0.7 for c in self.selected_color]

            if day_events:
                event_texts = "\n\n".join([event['schedule_value'] for event in day_events])
                event_text = f"{prev_day}\n\n{event_texts}"
                logging.info(f"{date_str}에 대한 이전 달 일정 추가: {event_texts}")  # 일정 로그
            else:
                event_text = str(prev_day)
                logging.info(f"{date_str}에 이전 달 일정 없음")  # 일정 없음 로그

            # 버튼 배경색의 밝기에 따라 글자 색상 변경
            brightness = self.calculate_brightness(darker_color)
            if brightness > 0.5:
                text_color = (0, 0, 0, 1)  # 밝으면 검정 글씨
            else:
                text_color = (1, 1, 1, 1)  # 어두우면 흰색 글씨

            btn = Button(
                text=event_text,
                background_normal='',  # 기본 배경 이미지 제거
                font_size='18',
                halign='left',
                valign='top',
                padding=(10, 10),
                font_name="NanumGothic.ttf",
                background_color=darker_color,  # 채도를 낮춘 배경색 설정
                color=text_color,  # 글자색 설정
                text_size=(self.width, None),
                on_press=lambda instance, m=self.month - 1: self.show_event_popup(instance, m))

            btn.bind(size=lambda instance, size: setattr(instance, 'text_size', size))
            calendar_grid.add_widget(btn)

        # 해당 월의 날짜와 일정 추가
        for day in range(1, last_day_of_month.day + 1):
            date_str = f"{self.year}-{self.month:02}-{day:02}"
            day_events = [event for event in current_month_events if event['schedule_day'][:10] == date_str]

            if day_events:
                event_texts = "\n\n".join([event['schedule_value'] for event in day_events])
                event_text = f"{day}\n\n{event_texts}"

                # supabase에서 받아온 btn_color 값이 있으면 해당 값을 사용하고, 없으면 None 반환
                btn_color_raw = day_events[0].get('btn_color', None)
                # btn_color_raw가 None이거나 빈 문자열일 경우
                if not btn_color_raw:
                    btn_color = None
                else:
                    btn_color = self.parse_color(btn_color_raw)

                # btn_color가 None일 경우 global_color로 대체
                if btn_color is None:
                    btn_color = self.selected_color  # global_color 사용
                    logging.info(f"Supabase에서 btn_color가 None 또는 빈 값으로 반환됨. Global color 사용: {btn_color}")

                logging.info(f"{date_str}에 대한 일정 추가: {event_texts}")  # 일정 로그
            else:
                event_text = str(day)
                btn_color = self.selected_color  # global color 적용
                logging.info(f"{date_str}에 일정 없음. 기본 색상 사용.")  # 일정 없음 로그

            # 버튼 배경색의 밝기에 따라 글자 색상 변경
            brightness = self.calculate_brightness(btn_color)
            if brightness > 0.5:
                text_color = (0, 0, 0, 1)  # 밝으면 검정 글씨
            else:
                text_color = (1, 1, 1, 1)  # 어두우면 흰색 글씨

            btn = Button(
                text=event_text,
                background_normal='',  # 기본 배경 이미지 제거
                font_size='18',
                halign='left',
                valign='top',
                padding=(10, 10),
                font_name="NanumGothic.ttf",
                background_color=btn_color,  # 배경색 설정
                color=text_color,  # 글자색 설정
                text_size=(self.width, None),
                on_press=lambda instance, m=self.month: self.show_event_popup(instance, m))


            btn.bind(size=lambda instance, size: setattr(instance, 'text_size', size))

            # 현재 날짜와 같은 날짜 버튼에 얇은 하얀색 테두리 추가
            if date_str == today_str:
                with btn.canvas.before:
                    # btn_color의 정반대 색상 계산
                    opposite_color = [1 - c for c in btn_color[:3]] + [btn_color[3]]  # RGB 각 색상의 정반대 색상 계산
                    Color(*opposite_color)  # 동적 색상 변환
                    # 초기 테두리 생성
                    line = Line(rectangle=(btn.x, btn.y, btn.width, btn.height), width=2)

                # 버튼 크기 변경 시 테두리 업데이트
                btn.bind(size=lambda instance, size: setattr(line, 'rectangle', (instance.x, instance.y, instance.width, instance.height)))

            calendar_grid.add_widget(btn)

        # 다음 달의 날짜와 일정 추가
        total_days_displayed = first_weekday + last_day_of_month.day
        next_month_day = 1
        while total_days_displayed < 35:  # 7 * 5 그리드를 위해 총 35칸 필요
            date_str = f"{self.year if self.month < 12 else self.year + 1}-{1 if self.month == 12 else self.month + 1:02}-{next_month_day:02}"
            day_events = [event for event in next_month_events if event['schedule_day'][:10] == date_str]
            # 다음 달 버튼: 글로벌 색상을 기반으로 채도 낮춘 색상 적용
            darker_color = [c * 0.7 for c in self.selected_color]

            if day_events:
                event_texts = "\n\n".join([event['schedule_value'] for event in day_events])
                event_text = f"{next_month_day}\n\n{event_texts}"
                logging.info(f"{date_str}에 대한 다음 달 일정 추가: {event_texts}")  # 일정 로그
            else:
                event_text = str(next_month_day)
                logging.info(f"{date_str}에 다음 달 일정 없음")  # 일정 없음 로그
            
            # 버튼 배경색의 밝기에 따라 글자 색상 변경
            brightness = self.calculate_brightness(darker_color)
            if brightness > 0.5:
                text_color = (0, 0, 0, 1)  # 밝으면 검정 글씨
            else:
                text_color = (1, 1, 1, 1)  # 어두우면 흰색 글씨

            btn = Button(
                text=event_text,
                background_normal='',  # 기본 배경 이미지 제거
                font_size='18',
                halign='left',
                valign='top',
                padding=(10, 10),
                font_name="NanumGothic.ttf",
                background_color=darker_color,  # 채도를 낮춘 배경색 설정
                color=text_color,  # 글자색 설정
                text_size=(self.width, None),
                on_press=lambda instance, m=self.month + 1: self.show_event_popup(instance, m))

            btn.bind(size=lambda instance, size: setattr(instance, 'text_size', size))
            calendar_grid.add_widget(btn)

            next_month_day += 1
            total_days_displayed += 1

    def show_event_popup(self, instance, month):
        # instance.text에서 일자 부분만 추출하여 두 글자까지 자름
        selected_day_str = instance.text.split("\n")[0][:2].strip()  # 버튼 텍스트의 첫 번째 줄만 두 글자로 자름
        selected_day = int(selected_day_str)  # int로 변환하여 날짜로 사용

        # 선택된 날짜를 기반으로 포맷
        selected_date = datetime(self.year, month, selected_day)
        formatted_date = selected_date.strftime("%Y-%m-%d")

        logging.info(formatted_date)

        # 선택된 날짜에 해당하는 이벤트를 찾아 미리 content_input에 입력
        day_events = [event for event in self.events if event['schedule_day'][:10] == formatted_date]

        # 팝업 내용 설정
        popup_content = EventPopup()
        popup_content.ids.date_label.text = f"선택한 날짜: {formatted_date}"

        # 선택한 날짜를 팝업에 전달
        popup_content.selected_date = formatted_date

        # 부모 레이아웃 설정
        popup_content.set_parent_layout(self)  # CalendarLayout 인스턴스를 전달

        if day_events:
            event_text = "\n".join([event['schedule_value'] for event in day_events])
            popup_content.ids.content_input.text = event_text  # content_input에 기존 일정 텍스트 채우기
        else:
            popup_content.ids.content_input.text = ""  # 일정이 없으면 빈 텍스트로 설정

        # 팝업 객체 생성 및 팝업을 content에 설정
        popup = ModalView(size_hint=(0.8, 0.6))  # ModalView 생성
        popup.add_widget(popup_content)  # ModalView에 EventPopup 추가

        # 팝업 객체를 EventPopup에 전달
        popup_content.set_popup(popup)

        # 팝업 열기
        popup.open()

    def go_to_next_month(self):
        """다음 달로 이동"""
        if self.month == 12:
            self.month = 1
            self.year += 1
        else:
            self.month += 1
        logging.info(f"다음 달로 이동: {self.year}-{self.month}")  # 다음 달 이동 로그
        self.update_calendar()

    def go_to_previous_month(self):
        """이전 달로 이동"""
        if self.month == 1:
            self.month = 12
            self.year -= 1
        else:
            self.month -= 1
        logging.info(f"이전 달로 이동: {self.year}-{self.month}")  # 이전 달 이동 로그
        self.update_calendar()

class EventPopup(BoxLayout):
    popup = None  # Popup 객체를 저장할 속성
    rounded_color = None  # 선택된 색상을 저장할 변수, 처음에는 None으로 설정

    def set_popup(self, popup_instance):
        """Popup 객체를 저장"""
        self.popup = popup_instance

    def set_parent_layout(self, layout_instance):
        """CalendarLayout 인스턴스를 저장"""
        self.parent_layout = layout_instance

    def submit_event(self, content):
        # selected_date는 이미 문자열이므로 변환 없이 사용
        formatted_selected_date = self.selected_date
        print(f"content 타입: {type(content)}")
        # 기존 이벤트를 가져오는 로직
        existing_event = supabase_helper.get_event_by_date(formatted_selected_date, self.parent_layout.supabase_client)

        # 색상을 선택하지 않았을 경우, 기존 색상을 유지
        if self.rounded_color is None and existing_event and existing_event.get("btn_color"):
            self.rounded_color = existing_event["btn_color"]
        
        # 이벤트 추가/업데이트 후, schedule_value와 btn_color가 비었는지 확인
        if not content.strip() and not self.rounded_color:
            # 디버깅: 조건이 만족되는지 확인
            print("조건 만족: content와 rounded_color가 비어 있음, row 삭제")
            # 만약 content와 btn_color가 모두 비었으면, Supabase에서 해당 날짜의 row 삭제
            supabase_helper.delete_empty_rows_for_date(
                formatted_date=formatted_selected_date,
                supabase_client=self.parent_layout.supabase_client
            )
            print(f"{formatted_selected_date}의 빈 row가 삭제되었습니다.")
        else:
            # Supabase에 업데이트 또는 추가
            print("조건 불만족: row 업데이트 또는 추가")
            supabase_helper.upsert_event_to_supabase(
                date=formatted_selected_date,
                value=content,
                btn_color=self.rounded_color,
                supabase_client=self.parent_layout.supabase_client
            )
            print(f"일정이 성공적으로 저장되었습니다: {formatted_selected_date}")
        self.parent_layout.refresh_calendar()
        
        if self.popup:
            self.popup.dismiss()  # 팝업 창 닫기


    def setLocalColor(self):
        color_picker = ColorPicker()
        color_picker.bind(color=self.on_color)
        popup = ModalView(size_hint=(0.8, 0.8), padding=20)
        popup.add_widget(color_picker)
        popup.open()

    def on_color(self, instance, color):
        # 색상 값을 반올림하여 2자리 소수로 변환
        self.rounded_color = [round(c, 2) for c in color]
        logging.info(f"선택한 색상: {self.rounded_color}")
        # 여기에서 선택된 색상을 다른 곳에 사용할 수 있습니다.

    def clearLocalColor(self):
        """버튼 색상을 초기화하고 Supabase에서 해당 날짜의 btn_color를 null로 설정"""
        formatted_date = self.selected_date  # 선택한 날짜를 참조하는 속성으로 설정해야 합니다.
        
        # Supabase 클라이언트 생성
        supabase_client = supabase_helper.create_supabase_client()
        
        # btn_color를 null로 업데이트
        success = supabase_helper.clear_color_for_date(formatted_date, supabase_client)
        if success:
            print(f"{formatted_date}의 btn_color가 성공적으로 초기화되었습니다.")
        else:
            print("btn_color 초기화에 실패했습니다.")

    def get_global_color_from_supabase(self):
        """Supabase에서 global_color를 가져오는 함수"""
        username = self.parent_layout.get_logged_in_username()  # CalendarLayout에서 로그인된 사용자 이름을 가져옴
        global_color = supabase_helper.get_global_setting(username, self.parent_layout.supabase_client)
        if global_color and 'global_color' in global_color:
            return self.parent_layout.parse_color(global_color['global_color'])  # global_color를 파싱하여 반환
        else:
            logging.info("global_color를 찾을 수 없으므로 기본 색상(흰색)을 사용합니다.")
            return [1, 1, 1, 1]  # 기본 흰색 반환

class CalendarApp(App):
    def build(self):
        return CalendarLayout()

if __name__ == '__main__':
    CalendarApp().run()