from PyQt5 import QtWidgets, QtCore, uic, QtGui
from PyQt5.QtGui import *
import sys, re
import serial
import threading
import uartSerial
import time

class MainWindow(QtWidgets.QMainWindow):
    appendResultTextSignal = QtCore.pyqtSignal(str)
    def __init__(self, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent)
        self.ui = uic.loadUi("main.ui", self)
        self.ui.show()
        self.setValues()

    def connectBtnClicked(self):
        uartSerial.openSerial(self.comport.text().strip(), int(self.boadrate.text().strip()))
        self.ser = uartSerial.getSerialConnection()
        thread = threading.Thread(target=self.logThread)
        thread.start()
        thread2 = threading.Thread(target=self.test)
        thread2.start()
        self.connectBtn.setEnabled(False)

    def test(self):
        try:
            #ser = serial.Serial('COM3',115200)
            time.sleep(1)
            self.ser.write("\n".encode())
            self.ser.write("debug\n".encode())
            while not self.shell_state:
                self.checkCurrentState()
                time.sleep(1)
            print("done!")
            self.setPmlogCtl(self.ctl_list)
            self.ser.write("tail -f /var/log/messages &\n".encode())
        except Exception as e:
            print(" Caught exception2 %s : %s" % (e.__class__,e))

    def setValues(self):
        self.status = ["NoDebug","Disable","NoShell","Shell"]
        # self.currentStatus = 0
        self.getLog = True
        self.shell_state = False
        self.lines = []
        self.ctl_list = ["playerfactory.default", "playerfactory.feed", "media.drmcontroller", "playready", "cdmi", "cdmi.playready", "chromium*"]
        self.appendResultTextSignal.connect(self.putResultToWindow)
        self.filter_pattern = {"state":"All", "name":"All", "msg":"All"}
        self.filters = {"state":["All"], "name":["All"], "msg":["All"]}
        self.pmLogCtlCombo.addItems(self.filters["name"])
        self.logCaseCombo.addItems(self.filters["state"])
        self.all_logs = []
        self.all_logs_count = 0
        self.logWin.setColumnCount(3)
        self.logWin.insertRow(self.all_logs_count)
        self.boadrate.setText("115200")
        self.comport.setText("COM3")

        # self.all_log_widget_model = QStandardItemModel(self.logWin)
        # self.logWin.setModel(self.all_log_widget_model)
        # self.logWin.show()

    def putResultToWindow(self, str):
        self.textBrowser.append(str)

        item = self.divPmLogLine(str)
        if item != None:
            log_state, pm_ctl_name, log_message = item
            # print(log_state, pm_ctl_name, log_message)
            state_item = QtWidgets.QTableWidgetItem(log_state)
            name_item = QtWidgets.QTableWidgetItem(pm_ctl_name)
            msg_item = QtWidgets.QTableWidgetItem(log_message)
            # self.logWin.setRowCount(self.all_logs_count)
            self.logWin.setItem(self.all_logs_count, 0, state_item)
            self.logWin.setItem(self.all_logs_count, 1, name_item)
            self.logWin.setItem(self.all_logs_count, 2, msg_item)
            self.setFilter(index=int(self.all_logs_count))
            self.all_logs_count += 1
            self.logWin.insertRow(self.all_logs_count)
            self.logWin.resizeColumnsToContents()
            self.logWin.resizeRowsToContents()
            self.logWin.verticalScrollBar().setValue(self.logWin.verticalScrollBar().maximum())


        # else:
        #     print("??")

        # self.all_logs_count += 1
        # item = QStandardItem(str)
        # self.all_log_widget_model.appendRow(item)
        # index = self.all_log_widget_model.indexFromItem(item)

    def closeEvent(self, event):
        try:
            print("CloseEvent")
            uartSerial.closeSerialConnection()
            QtWidgets.QMainWindow.closeEvent(self, event)
        except Exception as e:
            print(" Caught exception3 %s : %s" % (e.__class__,e))

    def divPmLogLine(self, line):
        # 2019-03-13T06:15:47.088069Z [3973.499459185] user.debug WebAppMgr [] playerfactory.default DBGMSG {} {"CODE_POINT":"<custompipeline.cpp:checkAppSrcBuffer(4037)>"} not Play State
        # pattern = '\S*\s*\S*\s*(user.\w+)\s*\S*\s*\S*\s*(\w+\.*\w*)\s*\S*\s*\S*\s*\S*\s*(.+)'
        pattern = '\d+-\d+-[\d\w:.]+\s+\[\d+\.\d+\]\s+(user\.\w+)\s+\w+\s+\[\]\s+(\w+\.\w+)\s+\w+(.+)'
        module = re.search(pattern, line)
        if module:
            log_state = module.group(1)
            pm_ctl_name = module.group(2)
            log_message = module.group(3)
            if log_state not in self.filters["state"]:
                self.filters["state"].append(log_state)
                self.logCaseCombo.insertItem(0, log_state)
            if pm_ctl_name not in self.filters["name"]:
                self.filters["name"].append(pm_ctl_name)
                self.pmLogCtlCombo.insertItem(0, pm_ctl_name)
            return (log_state, pm_ctl_name, log_message)
        else:
            print("None!!!!!!!!")
            return None

    def logThread(self):
        try:
            #ser = serial.Serial('COM3',115200)
            # self.ser = uartSerial.getSerialConnection()
            line = []
            while self.getLog:
                for c in self.ser.read(): # 1글자씩 받아옴
                    line.append(chr(c))
                    # print('chr(c)= ',chr(c))
                    if c == 10: # 10 == \n 줄바꿈.
                        msg = ''.join(line)
                        if msg.strip() != '':
                            self.lines.append(msg)
                            self.appendResultTextSignal.emit(msg)
                            del line[:]
        except Exception as e:
            print(" Caught exception1 %s : %s" % (e.__class__,e))


    def checkCurrentState(self):
        # self.ser.write("\n".encode())
        current_logs = ''.join(self.lines)
        if "ORG MAIN" in current_logs:
            self.ser.write("sh\n".encode())
            del self.lines[:]
        elif "/ #" in current_logs:
            self.shell_state = True
            del self.lines[:]
        elif "debug message disable" in current_logs:
            print("??????????")
            self.ser.write(120) # F9
            del self.lines[:]
        elif current_logs.strip() == '':
            self.ser.write("debug\n".encode())


    def setPmlogCtl(self, ctl_list):
        def_cmd = "PmLogCtl def {}\n"
        set_cmd = "PmLogCtl set {} debug\n"
        for ctl in ctl_list:
            def_ctl = def_cmd.format(ctl)
            set_ctl = set_cmd.format(ctl)
            self.ser.write(def_ctl.encode())
            print(def_ctl)
            self.ser.write(set_ctl.encode())
            print(set_ctl)


    def sendBtnClicked(self):
        try:
            inputText = self.lunaTextEdit.text() + '\n'
            #self.logWin.append(inputText)
            #ser.write(inputText.encode("utf-8"))
            self.ser.write(inputText.encode())
        except Exception as e:
            print(" Caught exception sendBtnClicked %s : %s" % (e.__class__,e))

    def setFilter(self, index=None):
        filter_ctl = self.pmLogCtlCombo.currentText().strip()
        filter_state = self.logCaseCombo.currentText().strip()
        filter_another = self.addFilterEdit.text().strip()
        self.filter_pattern["name"] = filter_ctl
        self.filter_pattern["state"] = filter_state
        self.filter_pattern["msg"] = filter_another if filter_another != '' else "All"
        if index == None or type(index) != int:
            for i in range(self.logWin.rowCount()-1):
                match = False
                if self.filter_pattern["state"] == "All" and self.filter_pattern["name"] == "All" and self.filter_pattern["msg"] == "All":
                    match = True
                else:
                    match_state, match_name, match_msg = False, False, False
                    if self.filter_pattern["state"] != "All":
                        item = self.logWin.item(i, 0)
                        if self.filter_pattern["state"] in item.text():
                            match_state = True
                    else:
                        match_state = True
                    if self.filter_pattern["name"] != "All":
                        item = self.logWin.item(i, 1)
                        if self.filter_pattern["name"] in item.text():
                            match_name = True
                    else:
                        match_name = True

                    if self.filter_pattern["msg"] != "All":
                        item = self.logWin.item(i, 2)
                        if self.filter_pattern["msg"] in item.text():
                            match_msg = True
                    else:
                        match_msg = True

                    match = match_state and match_name and match_msg
                    # if self.filter_pattern["msg"] != "All":
                    #     item = self.logWin.item(i, 2)
                    #     if self.filter_pattern["msg"] in item.text():
                    #         match = True
                self.logWin.setRowHidden(i, not match)
        else:
            match = False
            if self.filter_pattern["state"] == "All" and self.filter_pattern["name"] == "All" and self.filter_pattern["msg"] == "All":
                match = True
            else:
                if self.filter_pattern["state"] != "All":
                    item = self.logWin.item(index, 0)
                    if self.filter_pattern["state"] in item.text():
                        match = True
                if self.filter_pattern["name"] != "All":
                    item = self.logWin.item(index, 1)
                    if self.filter_pattern["name"] in item.text():
                        match = True
                # if self.filter_pattern["msg"] != "All":
                #     item = self.logWin.item(index, 2)
                #     if self.filter_pattern["msg"] in item.text():
                #         match = True
            self.logWin.setRowHidden(index, not match)

    def startLogBtnClicked(self):
        if self.logStartBtn.text() == "Start":
            self.logStartBtn.setText("Pause")
            self.getLog = True
            thread = threading.Thread(target=self.logThread)
            thread.start()
        else:
            self.logStartBtn.setText("Start")
            self.getLog = False



if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    toolWindow = MainWindow(None)
    app.exec_()
