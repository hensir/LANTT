"""LANTT lan tcp transport"""
import sys
import socket
import ssl
from threading import Thread
from base64 import b64decode, b64encode
from pywifi import const, PyWiFi, Profile
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog
from PyQt5.QtCore import pyqtSlot, QDir, Qt, pyqtSignal
from PyQt5.QtGui import QColor
from ui_mainwindow import Ui_MainWindow
from dialog import DialogPort, DialogThread, DialogText, DialogGetIP


# TODO 异步IO
# TODO sendbin和getbin作为一个单独函数都是为了从主线程中批出来一个线程 而不影响主UI
# TODO 把整个文件的fileinfo都发给client    然后大小除以缓冲区的大小 这个就有了一个progressbar的max数值    最后recv一次就是一个step
# TODO 其实我想测试的是大文件 这样两个todo都可以进行
# TODO 传送文本和这个 停止服务还没做
# TODO

class Mymainwindow(QMainWindow):
    """我的窗体类"""

    def __init__(self, parent=None):
        """初始化窗体"""
        super().__init__(parent)  # 调用父类构造函数，创建窗体
        self.ui = Ui_MainWindow()  # 创建UI对象
        self.ui.setupUi(self)  # 构造UI界面
        self.setWindowTitle("LANTT")
        self._PortDialog = None  # 特殊的处理方法 共用的两个变量
        self._ThreadDialog = None
        # -----设置默认tab界面-----
        if sys.argv[0].find('client') == -1:  # 如果当前文件名中没有client字样就 默认tabServer
            self.ui.tabWidget.setCurrentIndex(0)
        else:
            self.ui.tabWidget.setCurrentIndex(1)
        # ------tabServer的设置------
        self.ui.StE.setTextColor(QColor(0, 255, 0))
        self._filelist = []
        self._ServerFileFolder = sys.argv[0][:sys.argv[0].rfind('/') + 1]
        self._ServerFFF = QDir(self._ServerFileFolder).entryList(QDir.Files | QDir.NoDot)  # 文件夹下的文件
        self._ServerPort = 23719
        self._ServerThreadNum = 2
        self._ServerText2Send = None
        self._textDialog = None
        self.ServerStatus = False  # 做给线程轮询判断 用来断开服务
        self.initStE()
        # ------tabClient的设置------
        self.ui.CtE.setTextColor(QColor(0, 255, 0))
        self._ClientFileFolder = sys.argv[0][:sys.argv[0].rfind('/') + 1]
        self._ClientConnIP = "192.168.6.120"
        self._ClientConnPort = 23719
        self._ClientThreadNum = 6
        self._ClientText2Recv = None
        self._ClientGetIPDialog = None
        self.ClientStatus = False  # 做给线程轮询判断 用来断开服务
        self.initCtE()

    def initStE(self):
        """程序开始时打印Ste要显示的文本"""
        text1 = "当前主机名为:\n" + socket.gethostname() + "\n"
        text2 = "当前IP地址为:\n" + socket.gethostbyname(socket.gethostname()) + "\n"
        text3 = "缺省端口为:\n" + str(self._ServerPort) + "\n"
        text4 = "发送线程数量为:\n" + str(self._ServerThreadNum) + "\n"
        text6 = ""
        # ------文件和文件夹只能显示一个------
        if self.ui.StB1.isChecked():
            text6 += "当前所选文件为:\n"
            for i in self._filelist:
                text6 += i + '\n'
        elif self.ui.StB2.isChecked():
            text6 += "当前所选文件夹为:\n"
            text6 += self._ServerFileFolder
            if len(self._ServerFFF) == 0:
                text6 += "\n该文件夹下没有文件"
            else:
                text6 += "\n该文件夹下有以下文件:"
            for filetext in self._ServerFFF:
                text6 += ("\n   %s" % filetext)
        elif self.ui.StB6.isChecked():
            text6 += "当前所选文本为:\n"
            text6 += self._ServerText2Send
        self.ui.StE.setText(text1 + text2 + text3 + text4 + text6)

        if self.ServerStatus:
            self.ui.statusBar.showMessage("当前服务已开启 请直接选择文件或者改变文本")
        else:
            self.ui.statusBar.showMessage("当前服务未开启")

    def initCtE(self):
        """程序开始时打印Cte要显示的文本"""
        text1 = "本机主机名为:\n" + socket.gethostname() + "\n"
        text2 = "本机IP地址为:\n" + socket.gethostbyname(socket.gethostname()) + "\n"
        text3 = "服务器IP地址为:\n" + str(self._ClientConnIP) + "\n"
        text4 = "服务器端口为:\n" + str(self._ClientConnPort) + "\n"
        text5 = "接收线程数量为:\n" + str(self._ClientThreadNum) + "\n"
        text6 = "接收文件地址为:\n" + self._ClientFileFolder
        self.ui.CtE.setText(text1 + text2 + text3 + text4 + text5 + text6)

        # if self.ClientStatus and (self.ui.tabWidget.currentIndex() != 1):
        #     self.ui.statusBar.showMessage("开始接收数据")
        # else:
        #     self.ui.statusBar.showMessage("数据接收已停止")

    # -------TabServer的按钮-------

    @pyqtSlot()
    def on_StB1_clicked(self):
        """选择文件按钮"""
        # -----改变按钮状态----
        self.ui.StB1.setChecked(True)
        self.ui.StB2.setChecked(False)
        self.ui.StB6.setChecked(False)

        # ------获取文件名---------
        curPath = QDir.currentPath()
        dlgTitle = "请选择要传送的文件"
        filt = "所有(*.*);;文本(*.txt);;图片(*.jpg *gif *png);;视频(*.mp4 *avi *mkv)"
        filelist, filtUsed = QFileDialog.getOpenFileNames(self, dlgTitle, curPath, filt)
        # ------检测用户有没有选---------
        if filelist:
            self._filelist = filelist[:]
            self.initStE()
        elif len(filelist) == 0 and len(self._filelist) == 0:
            self.ui.StB1.setChecked(False)
            self.ui.StB2.setChecked(True)
        elif len(filelist) == 0 and len(self._filelist) != 0:
            self.initStE()

    # cur 空 且 pre 空    取消操作回文件夹
    # cur 空 且 pre 有    初始化文本
    # cur 有 且 pre 空不空都要覆盖
    # self.ui.StE.append("\n"+filtUsed) # 选择文件时 所使用的过滤器

    @pyqtSlot()
    def on_StB2_clicked(self):
        """选择文件夹按钮"""
        # -----改变按钮状态----
        self.ui.StB1.setChecked(False)
        self.ui.StB2.setChecked(True)
        self.ui.StB6.setChecked(False)
        # ------获取文件夹---------
        curPath = QDir.currentPath()
        dlgTitle = "请选择要传送的文件夹"
        selectedDir = QFileDialog.getExistingDirectory(self, dlgTitle, curPath, QFileDialog.ShowDirsOnly)
        # ------检测用户有没有选---------
        if not selectedDir and self._ServerFileFolder:  # 因为folder经过初始化 所以不像file那样做三个检测
            pass
        else:
            self._ServerFileFolder = selectedDir
            # 从这里取文件夹下所有的文件名称 绝对路径
            self._ServerFFF = QDir(self._ServerFileFolder).entryList(QDir.Files | QDir.NoDot)
            print(self._ServerFFF)
            self.initStE()

    @pyqtSlot()
    def on_StB3_clicked(self):
        """设置端口按钮"""
        self._PortDialog = DialogPort(self)
        self._PortDialog.value2send.connect(self.do_setPort)
        self._PortDialog.exec()

    @pyqtSlot()
    def on_StB4_clicked(self):
        """设置线程按钮"""
        self._ThreadDialog = DialogThread(self)
        self._ThreadDialog.value2send.connect(self.do_setThreadnum)
        self._ThreadDialog.exec()

    @pyqtSlot()
    def on_StB5_clicked(self):
        wifi = PyWiFi()
        iface = wifi.interfaces()[0]
        self.ui.StE.append("网卡接口为\n" + iface.name())
        profile = Profile()
        profile.ssid = "LANTT"
        profile.auth = const.AUTH_ALG_OPEN
        profile.akm.append(const.AKM_TYPE_WPA2PSK)
        profile.cipher = const.CIPHER_TYPE_CCMP
        profile.key = "5607893124"
        tep_profile = iface.add_network_profile(profile)
        iface.connect(tep_profile)

    @pyqtSlot()
    def on_StB6_clicked(self):
        """传送文本按钮"""
        # -----改变按钮状态----
        self.ui.StB6.setChecked(True)
        self.ui.StB1.setChecked(False)
        self.ui.StB2.setChecked(False)
        # ------获取文件名---------
        self._textDialog = DialogText(self)
        self._textDialog.text2send.connect(self.do_setText2)
        self._textDialog.exec()
        # ------检测用户有没有选---------
        if not self._ServerText2Send:
            self.ui.StB6.setChecked(False)  # 我没做上面两个按钮的状态保存
            self.ui.StB2.setChecked(True)  # 所以就手动指定了一个
            self._ServerFileFolder = sys.argv[0][:sys.argv[0].rfind('/') + 1]
        self.initStE()

    @pyqtSlot()
    def on_StB7_clicked(self):
        """开启服务按钮"""
        # -----改变按钮状态----
        # 这里主要开一个多线程
        self.ServerStatus = True
        self.ui.statusBar.showMessage("当前服务已开启 请直接选择文件或者改变文本")
        t = Thread(target=self.sendbin)
        t.start()

    @pyqtSlot()
    def on_StB8_clicked(self):
        self.ServerStatus = False
        self.ui.statusBar.showMessage("当前服务已关闭")

    def sendbin(self):
        """专门用于发送二进制数据的静态函数"""
        # data应该是一个二进制的数据 我这个函数只是发送不做任何处理
        # 打包成一个元组或者字典吧
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.load_cert_chain(r".\python_test.cer", r".\python_test.key")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(('127.0.0.1', 6666))
            sock.listen(5)
            with context.wrap_socket(sock, server_side=True) as ssock:
                while True:
                    if self.ServerStatus:
                        print("本地服务端地址:s%s" % ssock.getsockname)
                        client, addr = ssock.accept()
                        print("客户端地址:%s:%s" % addr)  # 静态检查错误
                        if self.ui.StB1.isChecked():
                            # 打包 self._filelist     这里静态检查有误
                            for filename in [self._filelist]:
                                client.send(filename.encode('utf-8'))
                                print(filename)
                                with open(filename, 'rb') as f:
                                    data = b64encode(f.read())
                                client.sendall(data)
                                client.send(b'next')
                        elif self.ui.StB2.isChecked():
                            # 打包 self._ServerFFF
                            for filename in self._ServerFFF:
                                client.send(filename.encode('utf-8'))
                                print(filename)
                                with open(filename, 'rb') as f:
                                    data = b64encode(f.read())
                                client.sendall(data)
                                client.send(b'next')
                        elif self.ui.StB6.isChecked():
                            # 打包 self._ServerText2Send
                            client.send("text".encode('utf-8'))  # 我给了一个信号
                            print(self._ServerText2Send)
                            client.send(b64encode(self._ServerText2Send.encode('utf-8')))
                            print("编码后的字符串")
                            print(b64encode(self._ServerText2Send.encode('utf-8')))
                    else:
                        break
                    client.send(b'exit')
                    client.close()

    # -------TabClient的按钮-------
    servip2send = pyqtSignal(str)

    @pyqtSlot()
    def on_CtB1_clicked(self):
        """设置服务器IP按钮"""
        self._ClientGetIPDialog = DialogGetIP(self)
        # 这里用lambda 先把函数写出来
        self._ClientGetIPDialog.iptext2send.connect(self.setConnIP)
        self._ClientGetIPDialog.setLEvalue(5, self._ClientConnIP)
        self._ClientGetIPDialog.exec()

    def setConnIP(self, iptext):
        self._ClientConnIP = iptext
        self.initCtE()

    @pyqtSlot()
    def on_CtB2_clicked(self):
        """接收文件地址按钮"""
        curPath = QDir.currentPath()
        dlgTitle = "请选择要传送的文件夹"
        selectedDir = QFileDialog.getExistingDirectory(self, dlgTitle, curPath, QFileDialog.ShowDirsOnly)
        # ------检测用户有没有选---------
        if not selectedDir and self._ClientFileFolder:  # Ctrl+C 传统艺能
            pass
        else:
            self._ClientFileFolder = selectedDir + "/"
            self.initCtE()

    @pyqtSlot()
    def on_CtB3_clicked(self):
        """设置服务器端口按钮"""
        self._PortDialog = DialogPort(self)
        self._PortDialog.value2send.connect(self.do_setPort)
        self._PortDialog.exec()

    @pyqtSlot()
    def on_CtB4_clicked(self):
        """设置接收线程数量按钮"""
        self._ThreadDialog = DialogThread(self)
        self._ThreadDialog.value2send.connect(self.do_setThreadnum)
        self._ThreadDialog.exec()

    @pyqtSlot()
    def on_CtB5_clicked(self):
        """开启热点按钮"""
        pass

    @pyqtSlot()
    def on_CtB6_clicked(self):
        """接收文本按钮"""
        try:
            context = ssl._create_unverified_context()
            with socket.socket() as sock:
                with context.wrap_socket(sock, server_hostname='127.0.0.1') as ssock:
                    ssock.connect(('127.0.0.1', 6666))
                    print("本地地址:%s" % str(ssock.getsockname()))
                    # ----处理text----
                    filename = ssock.recv(1024).decode('utf-8')

                    if filename == "text":
                        self.ui.CtE.append("接收的文本为:")
                        in_data = bytes()
                        data = ssock.recv(1024)
                        while data:
                            in_data += data
                            data = ssock.recv(1024)
                            if data.decode('utf-8') == 'exit':
                                text = in_data.decode('utf-8')
                                # text = text.decode()
                                text = b64decode(text)
                                text = text.decode()

                                self.ui.CtE.append(text)
                        self.ui.CtE.append("文本接收结束")
                    return
        except ConnectionRefusedError as e:
            self.ui.CtE.append("连接失败")
            self.ui.statusBar.showMessage("数据接收连接失败")
            print(e)

    @pyqtSlot()
    def on_CtB7_clicked(self):
        """占位按钮"""

    @pyqtSlot()
    def on_CtB8_clicked(self):
        """开始/关闭接收按钮"""
        ButtonState = self.ui.CtB8.text()
        if ButtonState == "开启服务":
            self.ui.CtB8.setText("关闭服务")
            self.ui.statusBar.showMessage("数据接收已停止")
            self.ClientStatus = True
        else:
            self.ui.CtB8.setText("开启服务")
            self.ui.statusBar.showMessage("开始接收数据")
            self.ClientStatus = False

        t = Thread(target=self.getbin)
        t.start()

    def getbin(self):
        """用以多线程接收文件"""
        try:
            context = ssl._create_unverified_context()
            with socket.socket() as sock:
                with context.wrap_socket(sock, server_hostname='127.0.0.1') as ssock:
                    ssock.connect(('127.0.0.1', 6666))
                    print("本地地址:%s" % str(ssock.getsockname()))
                    # ----处理text----
                    while True:
                        if self.ClientStatus:
                            filename = ssock.recv(1024).decode('utf-8')
                            # ----处理文件----
                            if not filename or filename == 'exit':
                                print(filename)
                                break
                            self.ui.CtE.append("文件名为:%s" % filename)

                            in_data = bytes()
                            data = ssock.recv(1024)
                            while data:
                                in_data += data
                                data = ssock.recv(1024)
                                if data.decode('utf-8') == 'next':
                                    break
                            # 如果CFF的最后一个元素不是斜杠
                            if self._ClientFileFolder[-1] != "/":
                                self._ClientFileFolder += "/"
                            with open(self._ClientFileFolder + filename, 'wb') as f:
                                f.write(b64decode(in_data))
                            self.ui.CtE.append(filename + " 传输完成")
                        else:
                            break
        except ConnectionRefusedError as e:
            self.ui.statusBar.showMessage("数据接收连接失败")
            self.ui.CtB8.setText("开启服务")
            print(e)
            return
        self.ui.CtE.append("文件接收结束")
        self.ui.CtB8.setText("开启服务")

    # -------------自定槽函数------------
    @pyqtSlot(int)
    def do_setPort(self, value):
        if self.ui.Stab.isVisible():  # 如果Server的tab可见 就把对话框传来的数值赋给server 并初始化StE
            self._ServerPort = value
            self.initStE()
        else:
            self._ClientConnPort = value
            self.initCtE()

    @pyqtSlot(int)
    def do_setThreadnum(self, value):
        if self.ui.Stab.isVisible():
            self._ServerThreadNum = value
            self.initStE()
        else:
            self._ClientThreadNum = value  # 否则赋值给client 并初始化CtE
            self.initCtE()

    @pyqtSlot(str)
    def do_setText2(self, text):
        self._ServerText2Send = text
        self.initStE()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    form = Mymainwindow()
    form.show()
    sys.exit(app.exec())
