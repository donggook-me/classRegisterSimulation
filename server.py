# server.py
import sys
import json
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import socket
import threading


class ServerThread(QThread):
    messageReceived = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.resource_lock = threading.Lock()
        self.classDict = {"korean": [], "english": [], "chinese": []}
        self.classLimit = 1
        self.clients = {}

    def run(self):
        host = '127.0.0.1'
        port = 12345

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((host, port))
        server_socket.listen(5)

        while True:
            client_socket, addr = server_socket.accept()
            client_handler = ClientHandler(client_socket)
            self.handle_new_client(client_handler)

            client_handler.messageReceived.connect(self.handle_message)
            client_handler.start()

    def handle_message(self, message):
        jsonMessage = json.loads(message)
        clientName = jsonMessage['clientName']
        type = jsonMessage['type']

        if type == "REQUEST_CLASS":
            # print("reqeust comes..")
            className = jsonMessage['className']
            self.handle_resource_request(clientName, className)

        elif type == "RELEASE_CLASS":
            # print("release start..")
            className = jsonMessage['className']
            self.handle_resource_release(clientName, className)
        else:
            updatetxt = f"{clientName} : {jsonMessage['msg']}"
            self.serverWindow.update_text(updatetxt)
            self.broadcast_message(jsonMessage['msg'], clientName)

    def handle_resource_request(self, clientName, className):
        DONE = False
        if len(self.classDict[className]) < self.classLimit:
            with self.resource_lock:
                self.classDict[className].append(clientName)
                DONE = True
                self.return_resource_message('REQUEST_CLASS_SUCCEED', className, clientName)
                # 전체 유저를 대상으로 해당 클래스가 꽉 찼음을 알린다.
                if len(self.classDict[className]) == self.classLimit:
                    self.broadcast_class_status("CLASS_FULL", className)

        if not DONE:
            self.return_resource_message('REQUEST_CLASS_FAIL', className, clientName)

    def handle_resource_release(self, clientName, className):
        DONE = False
        if clientName in self.classDict[className]:
            with self.resource_lock:
                self.classDict[className].remove(clientName)
                DONE = True
                # 한 유저가 한 과목을 수강포기했을 경우, 해당 클래스를 오픈 상태로 바꾸는 브로드캐스팅
                if len(self.classDict[className]) == (self.classLimit - 1):
                    self.broadcast_class_status("CLASS_OPEN", className)
                else:
                    self.return_resource_message('RELEASE_CLASS_SUCCEED', className, clientName)
        if not DONE:
            self.return_resource_message('RELEASE_CLASS_FAIL', className, clientName)

    # 일반 채팅 관련 broadcasting 포멧
    def broadcast_message(self, message, senderName):
        return_message = {
            'type': 'chat',
            'content': {
                'sender': senderName,
                'message': message
            }
        }
        print("---")
        print(return_message)
        print("---")
        # 브로드캐스팅 기능 추가
        for clientHandler in self.clients.values():
            clientHandler.send_msg(return_message)

    # 수강신청 성공 / 포기 관련된 1:1 리턴 메세지 포멧
    # type : RELEASE_CLASS_SUCCEED / RELEASE_CLASS_FAIL / REQUEST_CLASS_SUCCEED / REQUEST_CLASS_FAIL
    def return_resource_message(self, type, className, clientName):
        return_message = {
            'type': type,
            'className': className
        }
        self.clients[clientName].send_msg(return_message)

    # 수강신청 / 성공 관련 broadcasting 포멧
    # type : CLASS_FULL / CLASS_OPEN
    def broadcast_class_status(self, type, className):
        ownedClients = self.classDict[className]
        return_message = {
            'type': type,
            'className': className
        }
        for clientHandler in self.clients.values():
            if clientHandler.client_name not in ownedClients:
                clientHandler.send_msg(return_message)

    # 신규 클라이언트 접속시 닉네임 등록하는 코드
    def handle_new_client(self, client_handler):
        clientName = client_handler.receive_data()
        client_handler.set_client_name(clientName)
        self.clients[clientName] = client_handler


class ClientHandler(QThread):
    messageReceived = pyqtSignal(str)

    def __init__(self, client_socket):
        super().__init__()
        self.client_socket = client_socket
        self.client_name = None

    def run(self):
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

    def receive_data(self):
        data = self.client_socket.recv(1024)
        return data.decode('utf-8')

    def set_client_name(self, nickname):
        self.client_name = nickname

    def send_msg(self, msg):
        self.client_socket.send(json.dumps(msg).encode("utf-8"))


class ServerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setGeometry(100, 100, 400, 300)
        self.setWindowTitle('Server')

        self.text_edit = QTextEdit(self)
        self.text_edit.setGeometry(10, 10, 380, 200)
        self.text_edit.setReadOnly(True)

        self.server_thread = ServerThread()
        self.server_thread.serverWindow = self
        self.server_thread.messageReceived.connect(self.update_text)
        self.server_thread.start()

    def update_text(self, message):
        self.text_edit.append(message)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    server_window = ServerWindow()
    server_window.show()
    sys.exit(app.exec_())