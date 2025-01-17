import sys 
import json
import requests
import os, shutil
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton, QMessageBox, QGroupBox, QHBoxLayout)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPalette, QColor
from datetime import datetime, timedelta
from dateutil import parser
from PyQt5.QtGui import QIcon

class ExamBoard(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        try:
            # 设置窗口标题和图标
            self.setWindowTitle('考试看板')
            self.setWindowIcon(QIcon('.\\icon\\Toolbox_icon.png'))
            self.setWindowFlags(Qt.FramelessWindowHint)  # 隐藏边框

            # 获取屏幕分辨率
            screen_resolution = QApplication.desktop().screenGeometry()
            screen_width, screen_height = screen_resolution.width(), screen_resolution.height()

            # 根据屏幕大小设置窗口大小
            self.setGeometry(0, 0, screen_width, screen_height)
            self.showFullScreen()

            self.central_widget = QWidget(self)
            self.setCentralWidget(self.central_widget)

            palette = QPalette()
            palette.setColor(QPalette.Window, QColor("black"))  # 设置窗口背景为黑色
            palette.setColor(QPalette.WindowText, QColor("white"))
            self.setPalette(palette)

            main_layout = QVBoxLayout(self.central_widget)
            main_layout.setSpacing(15)

            self.top_display = QLabel(self)
            self.top_display.setStyleSheet('font-family: "SimHei"; font-size: 24px; background-color: rgba(255, 255, 255, 0.1); color: white; border: none; padding: 15px; border-radius: 10px;')
            self.top_display.setFixedHeight(60)
            self.top_display.setAlignment(Qt.AlignCenter)
            main_layout.addWidget(self.top_display)

            # 创建右上角的关闭按钮布局
            top_right_layout = QHBoxLayout()
            top_right_layout.setAlignment(Qt.AlignRight)

            self.close_button = QPushButton('关闭', self)
            self.close_button.setStyleSheet('font-family: "SimHei"; font-size: 20px; background-color: rgba(255, 255, 255, 0.1); color: white; border: none; padding: 15px; border-radius: 10px;')  # 设置背景透明，白色透明感，圆角弧度
            self.close_button.clicked.connect(self.close)
            top_right_layout.addWidget(self.close_button)

            # 将右上角的关闭按钮布局添加到主布局的顶部
            main_layout.addLayout(top_right_layout)

            self.time_display = QLabel('', self)
            self.time_display.setStyleSheet('font-family: "SimHei"; font-size: 200px; padding: 15px; color: white; background-color: black;')  # 设置背景为黑色
            self.time_display.setAlignment(Qt.AlignCenter)
            main_layout.addWidget(self.time_display)

            self.exam_info_layout = QVBoxLayout()
            self.exam_info_layout.setAlignment(Qt.AlignCenter)
            main_layout.addLayout(self.exam_info_layout)

            footer_layout = QHBoxLayout()

            self.date_display = QLabel('', self)
            self.date_display.setStyleSheet('font-family: "SimHei"; font-size: 20px; background-color: rgba(255, 255, 255, 0.1); color: white; border: none; padding: 15px; border-radius: 10px;')  # 设置样式与顶部标题相同
            footer_layout.addWidget(self.date_display, alignment=Qt.AlignLeft)

            self.day_count_display = QLabel('', self)
            self.day_count_display.setStyleSheet('font-family: "SimHei"; font-size: 20px; background-color: rgba(255, 255, 255, 0.1); color: white; border: none; padding: 15px; border-radius: 10px;')  # 设置样式与顶部标题相同
            footer_layout.addWidget(self.day_count_display, alignment=Qt.AlignCenter)

            self.close_button_footer = QPushButton('关闭', self)
            self.close_button_footer.setStyleSheet('font-family: "SimHei"; font-size: 20px; background-color: rgba(255, 255, 255, 0.1); color: white; border: none; padding: 15px; border-radius: 10px;')  # 设置背景透明，白色透明感，圆角弧度
            self.close_button_footer.clicked.connect(self.close)
            footer_layout.addWidget(self.close_button_footer, alignment=Qt.AlignRight)

            config_layout = QHBoxLayout()

            self.config_button = QPushButton('配置', self)
            self.config_button.setStyleSheet('font-family: "SimHei"; font-size: 20px; background-color: rgba(255, 255, 255, 0.1); color: white; border: none; padding: 15px; border-radius: 10px;')  # 设置背景透明，白色透明感，圆角弧度
            self.config_button.clicked.connect(self.open_config_file)
            config_layout.addWidget(self.config_button, alignment=Qt.AlignRight)

            main_layout.addStretch()  # 添加一个伸缩项，使得底部的布局始终保持在底部
            main_layout.addLayout(config_layout)  # 将配置按钮布局添加到主布局
            main_layout.addLayout(footer_layout)  # 将底部布局添加到主布局

            self.timer = QTimer(self)
            self.timer.timeout.connect(self.update_time)
            self.timer.start(1000)

            # 使用 QTimer 在后台进行初始化
            QTimer.singleShot(0, self.initialize)
        except Exception as e:
            self.day_count_display.setText(f"初始化错误")



    def initialize(self):
        try:
            self.fetch_time_from_internet()
            self.load_exam_data()
        except Exception as e:
            self.day_count_display.setText(f"初始化错误")

    def fetch_time_from_internet(self):
        try:
            response = requests.get('http://worldtimeapi.org/api/timezone/Asia/Shanghai')
            current_time = response.json()['datetime']
            self.current_time = parser.isoparse(current_time).replace(tzinfo=None)  # 转换为offset-naive
        except requests.RequestException as e:
            self.current_time = datetime.now()
        self.update_time_display()

    def update_time(self):
        self.current_time += timedelta(seconds=1)
        self.update_time_display()

        # 检查是否过凌晨
        if self.current_time.hour == 0 and self.current_time.minute == 0 and self.current_time.second == 0:
            self.update_date_display()
            self.update_day_count_display()
            self.load_exam_data()

    def update_time_display(self):
        self.time_display.setText(self.current_time.strftime("%H:%M:%S"))
        self.date_display.setText(self.current_time.strftime("%Y-%m-%d"))

    def update_date_display(self):
        self.date_display.setText(self.current_time.strftime("%Y-%m-%d"))

    def update_day_count_display(self):
        try:
            with open('exam_data.json', 'r', encoding='utf-8') as file:
                exam_data = json.load(file)
                unique_dates = sorted({datetime.strptime(exam['date'], "%Y-%m-%d").date() for exam in exam_data.get('exams', [])})
                if unique_dates:
                    day_count = (self.current_time.date() - unique_dates[0]).days + 1
                    self.day_count_display.setText(f"今天是考试第 {day_count} 天")
                else:
                    self.day_count_display.setText("没有考试数据")
        except Exception as e:
            self.day_count_display.setText("更新考试天数错误")

    def load_exam_data(self):
        try:
            with open('exam_data.json', 'r', encoding='utf-8') as file:
                exam_data = json.load(file)
                self.populate_labels(exam_data)
                self.set_welcome_message(exam_data.get('welcome_message', '欢迎使用考试看板'))
        except Exception as e:
            self.day_count_display.setText("没有考试数据")

    def populate_labels(self, exam_data):
        try:
            # 清除现有考试信息
            for i in reversed(range(self.exam_info_layout.count())):
                widget = self.exam_info_layout.itemAt(i).widget()
                if widget is not None:
                    widget.deleteLater()

            current_date = self.current_time.date()  # 使用从网上获取的时间
            today_exams = []

            # 提取今天的考试信息
            for exam in exam_data.get('exams', []):
                exam_date = datetime.strptime(exam['date'], "%Y-%m-%d").date()
                if exam_date == current_date:
                    start_time = datetime.strptime(f"{exam['date']} {exam['start_time']}", "%Y-%m-%d %H:%M:%S")
                    end_time = datetime.strptime(f"{exam['date']} {exam['end_time']}", "%Y-%m-%d %H:%M:%S")
                    today_exams.append({
                        'subject': exam['subject'],
                        'start': start_time,
                        'end': end_time
                    })

            # 按开始时间排序
            sorted_exam_data = sorted(today_exams, key=lambda x: x['start'])

            if not sorted_exam_data:
                self.day_count_display.setText("今天没有考试信息")
                return

            now = self.current_time  # 使用从网上获取的时间
            ongoing_exam = None
            next_exam = None

            # 检查是否有正在进行的考试或下一场考试
            for exam in sorted_exam_data:
                if exam['start'] <= now <= exam['end']:
                    ongoing_exam = exam
                    break
                elif now < exam['start']:
                    next_exam = exam
                    break

            # 显示正在进行的考试倒计时
            if ongoing_exam:
                self.setup_countdown_label(ongoing_exam, "orange", "考试结束", exam_data)
            elif next_exam:
                self.setup_countdown_label(next_exam, "green", "考试开始", exam_data)

            # 显示所有未结束的考试信息
            for exam in sorted_exam_data:
                if exam['start'] < now <= exam['end']:  # 只显示未结束的考试信息
                    status_text, status_color = self.get_exam_status(exam, now)
                    group_box = QGroupBox()
                    layout = QVBoxLayout()

                    # 创建标签并设置文本
                    label = QLabel(f"科目: {exam['subject']} | 开始时间: {exam['start'].strftime('%H:%M:%S')} | 结束时间: {exam['end'].strftime('%H:%M:%S')} | 状态: {status_text}")
                    label.setAlignment(Qt.AlignCenter)  # 设置文本居中
                    label.setStyleSheet(f"font-family: 'SimHei'; font-size: 28px; color: {status_color};")  # 使用 status_color 作为文本颜色

                    layout.addWidget(label)
                    group_box.setLayout(layout)
                    group_box.setStyleSheet("""
                        background-color: rgba(255, 255, 255, 0.1); 
                        border-radius: 15px; 
                        padding: 5px;
                        color: white; 
                        border: none;
                    """)

                    self.exam_info_layout.addWidget(group_box)
                    self.exam_info_layout.addSpacing(10)

            # 不在考试时间显示未开考的考试信息
            for exam in sorted_exam_data:
                if now <= exam['start']:
                    if not ongoing_exam:  # 正在进行的考试已结束，显示未结束的考试信息
                        status_text, status_color = self.get_exam_status(exam, now)
                        group_box = QGroupBox()
                        layout = QVBoxLayout()

                        # 创建标签并设置文本
                        label = QLabel(f"科目: {exam['subject']} | 开始时间: {exam['start'].strftime('%H:%M:%S')} | 结束时间: {exam['end'].strftime('%H:%M:%S')} | 状态: {status_text}")
                        label.setAlignment(Qt.AlignCenter)  # 设置文本居中
                        label.setStyleSheet(f"font-family: 'SimHei'; font-size: 28px; color: {status_color};")  # 使用 status_color 作为文本颜色

                        layout.addWidget(label)
                        group_box.setLayout(layout)
                        group_box.setStyleSheet("""
                            background-color: rgba(255, 255, 255, 0.1); 
                            border-radius: 15px; 
                            padding: 5px;
                            color: white; 
                            border: none;
                        """)

                        self.exam_info_layout.addWidget(group_box)
                        self.exam_info_layout.addSpacing(10)


            # 计算考试天数
            unique_dates = sorted({datetime.strptime(exam['date'], "%Y-%m-%d").date() for exam in exam_data.get('exams', [])})
            if exam['end'] <= now:
                self.day_count_display.setText("今天的考试已经结束!")
            else:
                if unique_dates:
                    day_count = (current_date - unique_dates[0]).days + 1
                    self.day_count_display.setText(f"今天是考试第 {day_count} 天")
                else:
                    self.day_count_display.setText("没有考试数据")
        except Exception as e:
            self.day_count_display.setText("填充考试信息错误")




    

    def setup_countdown_label(self, exam, color, end_text, exam_data):
        try:
            countdown_label = QLabel(self)
            countdown_label.setStyleSheet(f"font-family: 'SimHei'; font-size: 30px; color: {color}; background-color: rgba(255, 255, 255, 0.1); border-radius: 10px; padding: 10px;")
            countdown_label.setAlignment(Qt.AlignCenter)
            self.exam_info_layout.addWidget(countdown_label)

            def update_countdown():
                now = self.current_time  # 使用从网上获取的时间
                remaining_time = exam['end'] - now if color == "orange" else exam['start'] - now
                if color == "orange":
                    remaining_time = exam['end'] - now
                    if remaining_time.total_seconds() > 0:
                        remaining_time += timedelta(seconds=1)
                else:
                    remaining_time = exam['start'] - now
                if remaining_time.total_seconds() > 0:
                    days, remainder = divmod(remaining_time.total_seconds(), 86400)
                    hours, remainder = divmod(remainder, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    if days > 0:
                        countdown_label.setText(f"剩余时间: {int(days)} 天 {int(hours)} 小时 {int(minutes)} 分钟 {int(seconds)} 秒")
                    elif hours > 0:
                        countdown_label.setText(f"剩余时间: {int(hours)} 小时 {int(minutes)} 分钟 {int(seconds)} 秒")
                    elif minutes > 0:
                        countdown_label.setText(f"剩余时间: {int(minutes)} 分钟 {int(seconds)} 秒")
                    else:
                        countdown_label.setText(f"剩余时间: {int(seconds)} 秒")
                else:
                    countdown_label.setText(end_text)
                    self.timer.timeout.disconnect(update_countdown)
                    self.populate_labels(exam_data)  # 重新加载考试信息

            self.timer.timeout.connect(update_countdown)
        except Exception as e:
            QMessageBox.critical(self, '设置倒计时标签错误', f'设置倒计时标签过程中发生错误: {e}')

    def get_exam_status(self, exam, now):
        if now < exam['start']:
            return "未开考", "green"
        elif exam['start'] <= now <= exam['end']:
            return "进行中", "orange"
        else:
            return "已结束", "red"

    def set_welcome_message(self, message):
        self.top_display.setText(message)

    def open_config_file(self):
        fixed_file_path = 'exam_data.json'  # 替换为你的固定文件路径
        try:
            os.startfile(fixed_file_path)
            QTimer.singleShot(200, self.handle)  # 延迟0.2秒后关闭程序
        except Exception as e:
            self.day_count_display.setText(f"打开配置文件错误")
    
    def handle(self):
        try:
            # 定义所有需要删除的文件和文件夹
            paths_to_delete = [
                os.path.join('Config', 'install_links'),
                os.path.join('Config', 'keys'),
                os.path.join('Config', 'download_links'),
                os.path.join('Downloads')
            ]
            
            # 遍历路径列表，删除存在的文件或文件夹
            for path in paths_to_delete:
                if os.path.exists(path):
                    if os.path.isdir(path):
                        shutil.rmtree(path)
                    else:
                        os.remove(path)
        except Exception as e:
            self.day_count_display.setText(f"删除文件或文件夹错误")

        # 关闭应用程序
        QApplication.instance().quit()  # 使用 PyQt 的 quit 来关闭应用程序

if __name__ == "__main__":
    app = QApplication(sys.argv)
    try:
        window = ExamBoard()
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        QMessageBox.critical(None, '主程序错误', f'主程序运行过程中发生错误: {e}')
