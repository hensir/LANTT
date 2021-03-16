import sys
import os
import socket
import time
import threading
from PyQt5.QtGui import QPalette, QBrush, QColor
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QObject
from PyQt5.QtWidgets import QDialog, QApplication, QLineEdit, QGroupBox, QToolButton, QMessageBox

from ui_dialog import Ui_Dialog as valueui
from ui_text2 import Ui_Dialog as text2ui
from ui_inputip import Ui_Dialog as getipui


class DialogPort(QDialog):
    value2send = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = valueui()  # 创建UI对象
        self.ui.setupUi(self)  # 构造UI界面
        self.setAttribute(Qt.WA_DeleteOnClose)  # 对话框关闭时自动删除
        self.setWindowFlag(Qt.WindowStaysOnTopHint)  # StayOnTop显示
        self.setWindowTitle("设置端口")
        # self.selectionModel.currentChanged.connect(self.do_currentChanged)
        self.ui.DtB1.clicked.connect(self.accept)
        self.ui.DtB2.clicked.connect(self.reject)
        # -----设置ui----
        self.setMaximumSize(191, 208)
        self.setMinimumSize(191, 208)
        # ----lcd-----
        self.ui.Dlcd.setDigitCount(5)
        self.ui.Dlcd.display(60000)
        # ----spinbox-----
        self.ui.DsB.setValue(60000)
        self.ui.DsB.setMinimum(1024)
        self.ui.DsB.setMaximum(65535)
        # ----slider-----
        self.ui.DhS.setMinimum(1024)
        self.ui.DhS.setMaximum(65535)
        self.ui.DhS.setValue(60000)

    def on_DsB_valueChanged(self, value):
        self.ui.DhS.setValue(int(value))
        self.ui.Dlcd.display(value)

    def on_DhS_valueChanged(self, value):
        self.ui.DsB.setValue(int(value))
        self.ui.Dlcd.display(value)

    def on_DtB1_clicked(self):
        self.value2send.emit(self._Cli)

    def on_DtB2_clicked(self):
        pass


class DialogThread(QDialog):
    value2send = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = valueui()
        self.ui.setupUi(self)
        self.setAttribute(Qt.WA_DeleteOnClose)  # 对话框关闭时自动删除
        self.setWindowFlag(Qt.WindowStaysOnTopHint)  # StayOnTop显示
        # self.setAttribute(Qt.WA_TranslucentBackground)  # 将Form设置为透明
        self.setWindowFlag(Qt.FramelessWindowHint)  # 将Form设置为无边框
        self.ui.DtB1.clicked.connect(self.accept)
        self.ui.DtB2.clicked.connect(self.reject)
        # -----设置ui----
        # self.setMaximumSize(324, 568)
        self.setMinimumSize(200, 368)
        # ----lcd-----
        self.ui.Dlcd.setDigitCount(2)
        self.ui.Dlcd.display(6)
        # ----spinbox-----
        self.ui.DsB.setValue(6)
        font = self.ui.DsB.font()
        font.setPointSize(71)
        self.ui.DsB.setFont(font)
        self.ui.DsB.setMinimum(1)
        self.ui.DsB.setMaximum(12)
        # ----slider-----
        self.ui.DhS.setMinimum(1)
        self.ui.DhS.setMaximum(12)
        self.ui.DhS.setValue(6)

    def on_DsB_valueChanged(self, value):
        self.ui.DhS.setValue(int(value))
        self.ui.Dlcd.display(value)

    def on_DhS_valueChanged(self, value):
        self.ui.DsB.setValue(int(value))
        self.ui.Dlcd.display(value)

    def on_DtB1_clicked(self):
        self.value2send.emit(self.ui.DsB.value())

    def on_DtB2_clicked(self):
        pass


# TODO 跑马灯暂时取消 我现在已经尝试了QPallete的方法和qss 一个失效 另一个炸线程还不稳定
# TODO

class DialogText(QDialog):
    text2send = pyqtSignal(str)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = text2ui()  # 创建UI对象
        self.ui.setupUi(self)  # 构造UI界面
        self.setAttribute(Qt.WA_TranslucentBackground)  # 将Form设置为透明
        self.setWindowFlag(Qt.FramelessWindowHint)  # 将Form设置为无边框
        self.setAttribute(Qt.WA_DeleteOnClose)  # 对话框关闭时自动删除
        self.setWindowFlag(Qt.WindowStaysOnTopHint)  # StayOnTop显示

    @pyqtSlot()
    def on_tB1_clicked(self):
        self.text2send.emit(self.ui.tE.toPlainText())


class DialogGetIP(QDialog):
    iptext2send = pyqtSignal(str)  # 发送ip

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = getipui()  # 创建UI对象
        self.ui.setupUi(self)  # 构造UI界面
        self.setAttribute(Qt.WA_TranslucentBackground)  # 将Form设置为透明
        self.setWindowFlag(Qt.FramelessWindowHint)  # 将Form设置为无边框
        # ----创建组件二维列表 以供各项重复声明使用----
        self._tBList = []
        self._orderLEList = []
        self._GBlist = self.findChildren(QGroupBox)  # 获取所有组盒子
        for GB in self._GBlist:  # 从每个组里获取所有的LE
            self._orderLEList.append(GB.findChildren(QLineEdit))
            self._tBList.append(GB.findChildren(QToolButton))

        # -----lineedit的设置-----
        for LEList in self._orderLEList:  # 现在LE是一个二维列表 6个一维 4个二维
            LEList.sort(key=lambda elem: elem.objectName())  # 对列表中的每个列表按照元素的objectName进行排序
            for LE in LEList:  # 所有的LE连接槽函数
                LE.textChanged.connect(lambda: self.do_LEHandle(self.sender().text(), self.sender()))
        # ------toolbutton的设置-----
        for tB in self._tBList:
            for tbWidget in tB:
                tbWidget.clicked.connect(lambda: self.do_SendIP(self.sender()))

        # ----设置本地IP到编辑框----
        self._host = socket.gethostbyname(socket.gethostname())
        self.setLEvalue(4, self._host)

        # ----编辑框跑马灯----
        # TODO 跑马灯  现在有七个组，所以我们可以做七彩虹啦 从基准颜色开始向下一个颜色递增渐变  我去，不会是七个if吧
        # TODO         self.gB_2.setStyleSheet("background-color: rgb(255, 165, 82);\n""")
        # TODO p141 5.2.3
        # self.setAutoFillBackground(True)
        # self.ui.gB_1.setStyleSheet("")
        # bru = QBrush()
        # bru.setColor(Qt.red)
        # pale = QPalette()
        # pale.setBrush(QPalette.Window, bru)
        # self.ui.gB_1.setPalette(pale)
        # # self.ui.gB1.setPalette(pale)
        # # pale.setColor(QPalette.Window, QColor(255, 0, 0))

        # t = threading.Thread(target=self.setqss)
        # t.setDaemon(True)
        # t.start()

    # -------------自定义槽函数------------

    # def setqss(self):
    #     while True:
    #         # for gB in self._GBlist:
    #         #     # 拼接字符串
    #         #     qsstext = "background-color: rgb(%s, %s, %s);" % (str(R), str(G), str(B))
    #         #     gB.setStyleSheet(qsstext)
    #         #     print(gB.styleSheet())
    #         #     # print(qsstext)
    #         #     R += 10
    #         #     G += 10
    #         #     B += 10
    #         #     if R > 255:
    #         #         R = 0
    #         #     if G > 255:
    #         #         G = 0
    #         #     if B > 255:
    #         #         B = 0
    #         #     time.sleep(0.1)
    #
    #         for R in range(254, 255, 5):
    #             for G in range(1, 255, 5):
    #                 for B in range(1, 255, 50):
    #                     for LEList in self._orderLEList:  # 现在LE是一个二维列表 6个一维 4个二维
    #                         for LE in LEList:  # 所有的LE连接槽函数
    #                             # qsstext = "background-color: rgb(%s, %s, %s);" % (str(R), str(G), str(B))
    #                             # LE.setStyleSheet(qsstext)
    #                             print(R, G, B)
    #                             # brush = QBrush()
    #                             # brush.setColor(QColor(R, G, B))
    #                             # LE.setPalette(QPalette(QBrush(QColor(R, G, B))))
    #                             # pale = QPalette()
    #                             # pale.setColor(QPalette.Window, QColor(R, G, B))
    #                             # LE.setPalette(QPalette(QPalette.Window, QColor(R, G, B)))
    #                             # 这厘米那是一个brush 里面做一个color rgb的
    #                             time.sleep(0.1)

    @pyqtSlot(str, QObject)
    def do_LEHandle(self, text, le):  # 发信号的LE的text LE本身
        if text.isdigit():  #
            print("是数字")
            if int(text) > 255:
                QMessageBox.warning(self, "错误", str(text) + " 不是有效项。请指定一个介于 1 和 255 间的值。")
                le.setText(str(text)[:-1])
            elif len(text) >= 3:  # 不转换int 可以减少一个bug 也就是如果text > 99 那个字符串如果是011或者099将不满足大于99的条件
                hor, ver = self.get_OrderIndex(le)
                if (ver + 1) < 4:
                    self._orderLEList[hor][ver + 1].setFocus()
        elif text == '':  # 三种情况数字 空值和其他字符(包括功能键)
            return
        elif text.find(".") != -1 or text.find("。") != -1:
            # ----修复[:-1]的不全面问题且光标位置不变----
            temptext = ""
            tempcursorposition = 0
            cursorposition = 0
            for char in text:
                if char.isdigit():
                    temptext += char
                else:
                    cursorposition = tempcursorposition
                tempcursorposition += 1
            le.setText(temptext)  # [:-1]只能确保最后一位的非数字修证 光标位置本来可以直接传过来的 不过这个手动实现了一下 感觉还行
            le.setCursorPosition(cursorposition)
            # ----光标跳转到下一个LineEdit----
            hor, ver = self.get_OrderIndex(le)
            if (ver + 1) < 4:
                self._orderLEList[hor][ver + 1].setFocus()
        else:
            print("报个警 删除一个字符\a")
            # ----修复[:-1]的不全面问题且光标位置不变----
            temptext = ""
            tempcursorposition = 0
            cursorposition = 0
            for char in text:
                if char.isdigit():
                    temptext += char
                else:
                    cursorposition = tempcursorposition
                tempcursorposition += 1
            le.setText(temptext)  # [:-1]只能确保最后一位的非数字修证 光标位置本来可以直接传过来的 不过这个手动实现了一下 感觉还行
            le.setCursorPosition(cursorposition)
        return

    @pyqtSlot(QObject)
    def do_SendIP(self, tb):
        # ----查找tB在二位列表中的位置----
        hor = ver = 0
        for tBWidget in self._tBList:
            try:
                hor += 1
                ver = tBWidget.index(tb)
            except ValueError:
                print("第%s排中没找到这个tB" % (hor - 1))
            else:
                break
        print("第%s排 第%s列" % (hor - 1, ver))
        # ----开始操作IP----
        iptext = ""
        num = 0
        for LE in self._orderLEList[hor - 1]:  # 看一下这个方法 用join的话 可能会更傻
            if LE.text() == "":
                print("第%s行中第%s个编辑框是空的" % (str(hor), str(num + 1)))
                return
            else:
                iptext += LE.text() + "."
            num += 1
        print(iptext[:-1])
        self.iptext2send.emit(iptext[:-1])
        self.accept()

    @pyqtSlot(int, str)
    def setLEvalue(self, gbindex, iptext):  # 第一个参数是指定的gB,第二个参数是以 . 分割的标准句号
        ip = iter(iptext.split("."))  # 把ip拆开 然后转为iterator
        for le in self._orderLEList[gbindex]:  # 直接指定列表的索引 然后 进行四次next
            le.setText(next(ip))
        self._orderLEList[6][0].setFocus()

    def get_OrderIndex(self, le):
        hor = 0  # 水平
        ver = 0  # 垂直
        for LEList in self._orderLEList:
            try:
                hor += 1
                ver = LEList.index(le)
            except ValueError:
                print("第%s排中没找到这个LE" % (hor - 1))
            else:
                break
        print("第%s排 第%s列" % (hor - 1, ver))
        return hor - 1, ver


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # form = DialogPort()
    # form = DialogThread()
    form = DialogGetIP()
    form.show()
    sys.exit(app.exec_())
