# client.py ver1.0
#-*- coding:utf-8 -*-
import sys
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QVBoxLayout, QGridLayout,QHBoxLayout
import socket
import json


class ClientThread(QThread):
    messageReceived = pyqtSignal(str)

    def __init__(self, host, port, client_window, client_name):
        super().__init__()
        self.host = host
        self.port = port
        self.client_socket = None  # Added client_socket attribute
        self.client_window = client_window
        self.client_name = client_name
        self.messageReceived.connect(self.handle_message)

    def run(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.host, self.port))
        self.client_socket.send(self.client_name.encode('utf-8'))

        while True:
            data = self.client_socket.recv(1024)
            if not data:
                break
            try:
                message = data.decode('utf-8')
                self.messageReceived.emit(message)
            except json.JSONDecodeError:
                # Handle the case when the received message is not a valid JSON
                print("Invalid JSON format:", data.decode('utf-8'))

    def handle_message(self, message):
        print()
        print(message)
        print()
        returnedMsg = json.loads(message)

        if (returnedMsg['type'] == 'chat'):
            # message chat
            showing_msg = f"{returnedMsg['content']['sender']} : {returnedMsg['content']['message']}"
            self.client_window.update_text(showing_msg)

        else:
            className = returnedMsg['className']
            box = self.client_window.boxes[className]

            if returnedMsg['type'] == 'REQUEST_CLASS_SUCCEED':
                box.button.setText("수강포기")
            elif returnedMsg['type'] == 'REQUEST_CLASS_FAIL':
                self.messageReceived.emit(returnedMsg['type'])
                print(returnedMsg['type'])

            elif returnedMsg['type'] == 'RELEASE_CLASS_SUCCEED':
                box.button.setText("수강신청")
            elif returnedMsg['type'] == 'RELEASE_CLASS_FAIL':
                self.messageReceived.emit(returnedMsg['type'])
                print(returnedMsg['type'])

            elif returnedMsg['type'] == 'CLASS_FULL':
                box.button.setEnabled(False)
            elif returnedMsg['type'] == 'CLASS_OPEN':
                box.button.setText("수강신청")
                box.button.setEnabled(True)

    def send_chat(self, message):
        request_message = {
            'type': 'chat',
            'clientName': self.client_name,
            'msg': message
        }

        self.client_socket.send(json.dumps(request_message).encode("utf-8"))

    def request_resource(self, className):
        request_message = {
            'type': 'REQUEST_CLASS',
            'clientName': self.client_name,
            'className': className
        }
        self.client_socket.send(json.dumps(request_message).encode("utf-8"))

    def release_resource(self, className):
        request_message = {
            'type': 'RELEASE_CLASS',
            'clientName': self.client_name,
            'className': className
        }
        self.client_socket.send(json.dumps(request_message).encode("utf-8"))


class ClientWindow(QWidget):
    def __init__(self, host, port, nickname=None):
        super().__init__()

        self.stu_num = nickname

        self.client_thread = ClientThread(host, port, self, nickname)
        self.client_thread.clientWindow = self
        self.client_thread.start()
        self.boxes = {}

        self.num_subject = 0 #장바구니 과목 수
        self.num_subject_finished = 0 #수강신청 완료한 과목 수
        self.credit_subject = 0 #수강신청 완료한 학점

        self.list_basket = [[["korean"],["국문학개론","화2B,3A,3B,목4A,4B,5A","3학점","조흥욱"],["1","한국어문학부\n국어국문학전공","전공선택","2 4 6 3 5 7 ","국문학개론","01","조흥욱","3.0 / 3.0 / 0.0","주","화2B,3A,3B,목4A,4B,5A\n북악관 2층 3호실"]],[["english"],["영어교육론","화2B,3A,3B,목2B,3A,3B","3학점","김효영"],["3-4","영어영문학부","전공선택","3 9 5 7 2 3","영어교육론","02","김효영","3.0 / 3.0 / 0.0","주","화2B,3A,3B,목2B,3A,3B\n북악관 4층 3호실"]],[["chinese"],["중국어문법","월5A,5B,6A,6B","2학점","전긍"],["2","중국학부\n중국어문전공","전공선택","3 9 7 3 4 5","중국어문법","01","전긍","2.0 / 2.0 / 0.0","주","월5A,5B,6A,6B\n북악관 7층 8호실"]]]
        self.classify_subject_info = ["학년(기)","배정학과","이수구분","교과목번호","교과목명","분\0반","교강사명","학점 / 이론 / 실습","주\0/\0야","강의시간 / 강의실"] #수강과목 정보 분류 리스트

        self.list_finished_subject = []

        self.initUI()

    def initUI(self):

        self.setWindowTitle('수강신청 체험')
        self.setGeometry(700, 200, 950, 700)  # window size
        self.setFixedSize(QSize(950, 700))

        # Label 설정
        label_top = QLabel('수강신청시스템 | 수강신청체험', self)
        label_top.setAlignment(Qt.AlignLeft)

        label_top2 = QLabel('2023학년도 | 겨울학기 | {stu_num}'.format(stu_num=self.stu_num), self)
        label_top2.setAlignment(Qt.AlignRight)

        label_top2sub = QLabel('수업계획서 조회 기간: 2023.12.04(월) 00:00~24:00  | 수강신청 기간 : 2023.12.04(월) 10:00 ~ 16:00', self)
        label_top2sub.setAlignment(Qt.AlignRight)

        label_top3 = QLabel('장바구니 과목 수/학점: 3과목 / 8학점')

        self.label_bom = QLabel('나의시간표 | 총 신청과목: {num} 과목 | 총 신청학점: {credit} 학점'.format(num=self.num_subject_finished, credit=self.credit_subject))

        # Style Sheet
        label_top3.setStyleSheet("color: #000000;"
                                 "background-color: #E2E6F0;"
                                 "border-radius: 5px")

        self.label_bom.setStyleSheet("color: #ffffff;"
                                "background-color: #0068CE;"
                                "border-radius: 5px")

        # font 설정
        self.font = label_top.font()
        self.font.setFamily('Times New Roman')
        self.font.setBold(True)  # Bold

        label_top.setFont(self.font)
        label_top2.setFont(self.font)
        label_top2sub.setFont(self.font)
        self.label_bom.setFont(self.font)


        # 위젯 추가
        hbox = QHBoxLayout()
        hbox.addWidget(label_top)
        hbox.addWidget(label_top2)
        hbox.setContentsMargins(15, 0, 15, 0)

        hbox2 = QHBoxLayout()
        hbox2.addWidget(label_top2sub)
        hbox2.setContentsMargins(15, 0, 15, 0)

        hbox4 = QHBoxLayout()
        hbox4.addWidget(label_top3)
        hbox4.setContentsMargins(15, 0, 15, 0)

        hbox5 = QHBoxLayout()
        hbox5.addWidget(self.label_bom)
        hbox5.setContentsMargins(15, 0, 15, 0)

        # 텍스트 마진
        label_top3.setContentsMargins(10, 30, 30, 30)  # 왼 위 오 아
        self.label_bom.setContentsMargins(10, 30, 30, 30)


        # 장바구니 목록
        self.grid_basket = QGridLayout()
        self.grid_basket.setContentsMargins(10, 0, 10, 0)

        for i in range(len(self.list_basket)):
            box = QVBoxLayout()
            self.create_subject_box(box, self.list_basket[i])
            self.boxes[self.list_basket[i][0][0]] = box

        # 수강신청 완료 과목 목록
        self.grid2 = QGridLayout()
        self.grid2.setContentsMargins(15, 0, 15, 0)

        # 나의시간표 상단 분류
        for i in range(len(self.classify_subject_info)):
            self.classify_label(self.classify_subject_info[i],i)

        vbox = QVBoxLayout()

        vbox.addLayout(hbox)
        vbox.addLayout(hbox2)
        vbox.addLayout(hbox4)
        vbox.setAlignment(Qt.AlignTop)
        vbox.addLayout(self.grid_basket)
        vbox.addLayout(hbox5)
        vbox.addLayout(self.grid2)

        self.setLayout(vbox)
        vbox.stretch(1)

        self.show()

    def classify_label(self, name, col):
        lbl = QLabel(name, self)

        lbl.setFont(self.font)
        lbl.setContentsMargins(10, 10, 10, 10)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("background-color: #F9FAFB")

        self.grid2.addWidget(lbl, 0, col)


    # 수강신청 성공한 과목 추가
    def finished_subject(self, info_subject):
        self.num_subject_finished += 1
        crdit_str = info_subject[1][2]
        self.credit_subject += int(crdit_str[0:1])

        for x in range(self.grid2.count()):
            self.grid2.itemAt(x).widget().deleteLater()

        #나의시간표 리스트에 추가 후, view
        self.list_finished_subject.append(info_subject)

        for i in range(len(self.classify_subject_info)):
            self.classify_label(self.classify_subject_info[i],i)

        for i in range(len(self.list_finished_subject)):
            for j in range(len(self.list_finished_subject[i][2])):
                lbl = QLabel(self.list_finished_subject[i][2][j], self)
                lbl.setContentsMargins(10,10,0,10)
                lbl.setAlignment(Qt.AlignCenter)
                self.grid2.addWidget(lbl,i+1,j)

        self.label_bom.setText('나의시간표 | 총 신청과목: {num} 과목 | 총 신청학점: {credit} 학점'.format(num=self.num_subject_finished, credit=self.credit_subject))



    # 수강신청 실패한 과목 삭제
    def deleted_subject(self, info_subject):
        self.num_subject_finished -= 1
        crdit_str = info_subject[1][2]
        self.credit_subject -= int(crdit_str[0:1])

        subject_name = info_subject[0][0]

        # 나의시간표 리스트에서 삭제 후, view
        for a in range(len(self.list_finished_subject)):
            if(self.list_finished_subject[a][0][0] == subject_name):
                del(self.list_finished_subject[a])
                break

        for x in range(self.grid2.count()):
            self.grid2.itemAt(x).widget().deleteLater()

        for i in range(len(self.classify_subject_info)):
            self.classify_label(self.classify_subject_info[i],i)

        for i in range(len(self.list_finished_subject)):
            for j in range(len(self.list_finished_subject[i][2])):
                lbl = QLabel(self.list_finished_subject[i][2][j], self)
                lbl.setContentsMargins(0, 10, 0, 10)
                lbl.setAlignment(Qt.AlignCenter)
                self.grid2.addWidget(lbl, i + 1, j)

        self.label_bom.setText('나의시간표 | 총 신청과목: {num} 과목 | 총 신청학점: {credit} 학점'.format(num=self.num_subject_finished, credit=self.credit_subject))


    def create_subject_box(self, group_box, info_subject):

        for i in range(4):
            lbl = QLabel(info_subject[1][i], self)
            group_box.addWidget(lbl)

        btn = QPushButton('수강신청', self)
        btn.setCheckable(True)
        btn.clicked.connect(lambda: self.resource_handler(info_subject))
        group_box.addWidget(btn)
        group_box.button = btn

        group_box.setContentsMargins(50, 50, 50, 50)

        self.grid_basket.addLayout(group_box, 0, self.num_subject)
        self.num_subject += 1


    def send_message(self):
        message = self.input_line.text()
        self.client_thread.send_chat(message)
        self.input_line.clear()

    def update_text(self, message):
        self.chat_archive.append(message)

    def send_message(self):
        message = self.input_line.text()
        self.client_thread.send_chat(message)
        self.input_line.clear()

    def resource_handler(self,info_subject):
        subject_name = info_subject[0][0]
        print("수강신청 완료: ",subject_name)
        if self.boxes[subject_name].button.text() == "수강신청":
            self.client_thread.request_resource(subject_name)

            #나의시간표에 추가
            self.finished_subject(info_subject)
        else:
            self.client_thread.release_resource(subject_name)

            #나의시간표에서 삭제
            self.deleted_subject(info_subject)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    if (len(sys.argv) > 1):
        name = sys.argv[1]
        host = '127.0.0.1'
        port = 12345
        client_window = ClientWindow(host, port, name)
        client_window.show()
    sys.exit(app.exec_())