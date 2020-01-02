from GUI_PI import Ui_MainWindow
import sys, time, threading, random
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QWidget, QInputDialog, QLineEdit, QFileDialog
import time, datetime, os, shutil, queue
import csv, random, threading, platform, socket
import platform
import pickle
import json
from contextlib import closing
from pypjlink import Projector
from operator import itemgetter
import datetime

########## imran ###########
from PyQt5 import Qt
from PyQt5.QtOpenGL import *
# import cv2 as cv
from PIL import Image

############################

####### Imran ############
global tabActivity, tabCount
tabActivity = list()
tabCount = int()

try:
    if os.path.exists("Preview") != True:
        os.mkdir("Preview")
    if os.path.exists("Download") != True:
        os.mkdir("Download")
except Exception as e:
    print(e, "(Making of Download Dir)")



global imgTab

imgTab = [0, 0, 0, 0, 0, 0]

global imgShowList

imgShowList = ['', '', '', '', '', '']

global imgShow

imgShow = [False, False, False, False, False, False]

global down_status

down_status = True

global imgCount, totalImage
imgCount = int()
totalImage = int()

progressBarValue = 0

progressBarValue2 = 0

global dCount

dCount = 0

downloadList = list()

global down_q, upload_q
down_q = queue.Queue()
upload_q = queue.Queue()
u_filename = str()
uploadList = list()
uCount = 0
###########################


MyOS = platform.system().lower()
MyOS = 'linux'
print(MyOS)

host = '192.168.2.10'
# host = 'localhost'

Threads = list()

Table_updater = False

Expected_IDs = list()
try:
    os.makedirs('Host_config')
except:
    pass
try:
    with open('Host_config/expected_ids.pkl', 'rb') as fp:
        Expected_IDs = pickle.load(fp)
except:
    pass

Camera_configs = dict()


try:
    data = "101,102,103,104,105,106"
    if os.path.isfile("Host_config/prev_idlist.txt") != True:
        with open("Host_config/prev_idlist.txt", "w", encoding="utf-8") as f:
            f.write(data)
            print("Data Written")
except Exception as e:
    print(e, " - Error while creating file")

Capture_now = False
Projector_sysc = False
All_projectors = []


class MyGui(Ui_MainWindow, QtWidgets.QWidget):
    def __init__(self, dialog):
        Ui_MainWindow.__init__(self)
        QtWidgets.QWidget.__init__(self)
        self.setupUi(dialog)


class myMainClass():
    def __init__(self):

        # self.update_table()

        GUI.control_pushButton_capture.clicked.connect(self.control_pushButton_capture)
        # GUI.control_pushButton_refreshIPs.clicked.connect(self.control_pushButton_refreshIPs)
        GUI.control_pushButton_refreshSysStat.clicked.connect(self.control_pushButton_refreshSysStat)
        GUI.control_pushButton_camReboot.clicked.connect(self.control_pushButton_camReboot)
        GUI.control_pushButton_camStop.clicked.connect(self.control_pushButton_camStop)
        GUI.config_pushButton_cameraConf.clicked.connect(self.config_pushButton_cameraConf)
        GUI.config_pushButton_projectorSync.clicked.connect(self.config_pushButton_projectorSync)
        GUI.control_pushButton_GPIOon.clicked.connect(self.control_pushButton_GPIOon)
        GUI.control_pushButton_GPIOoff.clicked.connect(self.control_pushButton_GPIOoff)
        GUI.config_pushButton_rebootPi.clicked.connect(self.config_pushButton_rebootPi)
        GUI.config_pushButton_shutdownPi.clicked.connect(self.config_pushButton_shutdownPi)

        GUI.control_textEdit_expectedPiList.textChanged.connect(self.control_textEdit_expectedPiList)

        GUI.control_textEdit_expectedPiList.setText(','.join(Expected_IDs))

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.tick)
        self.timer.start(5000)

        self.timer2 = QtCore.QTimer()
        self.timer2.timeout.connect(self.tick2)
        self.timer2.start(50)

        self.load_camera_configs()

        ############ imran #################
        GUI.prev_pushButton_download.clicked.connect(self.prev_pushButton_download)
        GUI.pushButton_selectfile.clicked.connect(self.selectfile)
        GUI.pushButton_upload.clicked.connect(self.codeupload)
        GUI.prev_pushButton_preview.clicked.connect(self.prev_pushButton_preview)
        GUI.prev_pushButton_delete.clicked.connect(self.prev_pushButton_delete)
        GUI.prev_pushButton_refreshList.clicked.connect(self.tabCheck)
        GUI.prev_pushButton_refreshList2.clicked.connect(self.tabCheck)
        GUI.prev_label_status.setText("Preview")
        GUI.prev_label_status_D.setText("Download")
        GUI.down_textEdit.setText(str(datetime.datetime.now()))
        try:
            with open("Host_config/prev_idlist.txt", "r", encoding="utf-8") as f:
                data = f.read()
        except Exception as e:
            print(e)
        GUI.prev_lineEdit_ids.setText(data)

        self.timer3 = QtCore.QTimer()
        self.timer3.timeout.connect(self.show_image)
        self.timer3.start(100)

        self.progressBar = QtCore.QTimer()
        self.progressBar.timeout.connect(self.pUpdate)
        self.progressBar.start(100)
        self.showTextt = QtCore.QTimer()
        self.showTextt.timeout.connect(self.showText)
        self.showTextt.start(100)
        ####################################

    def tick(self):
        global All_projectors

        self.control_pushButton_refreshIPs()

        GUI.config_textEdit_projector.clear()
        for p in All_projectors:
            GUI.config_textEdit_projector.append(p)

    def tick2(self):
        global Table_updater
        if Table_updater:
            Table_updater = False
            self.control_pushButton_refreshIPs(pingClients=False)

    def load_camera_configs(self):
        global Camera_configs
        try:
            with open('Host_config/Camera_configs.pkl', 'rb') as fp:
                Camera_configs = pickle.load(fp)
                conf_NP = Camera_configs.get('camera')
                conf_Delay = Camera_configs.get('delay')

                print(conf_NP)

                for i in range(1, GUI.config_tableWidget_cameraConfN.rowCount()):
                    try:
                        header = GUI.config_tableWidget_cameraConfN.verticalHeaderItem(i).text()
                        GUI.config_tableWidget_cameraConfN.setItem(i, 0,
                                                                   QtWidgets.QTableWidgetItem(conf_NP.get(header)[0]))
                    except Exception as e:
                        print('a', e)
                        pass

                    try:
                        header = GUI.config_tableWidget_cameraConfP.verticalHeaderItem(i).text()
                        GUI.config_tableWidget_cameraConfP.setItem(i, 0,
                                                                   QtWidgets.QTableWidgetItem(conf_NP.get(header)[1]))
                    except Exception as e:
                        print('b', e)
                        pass

                for i in range(GUI.config_tableWidget_delayConf.rowCount()):
                    try:
                        header = GUI.config_tableWidget_delayConf.verticalHeaderItem(i).text()
                        GUI.config_tableWidget_delayConf.setItem(i, 0,
                                                                 QtWidgets.QTableWidgetItem(conf_Delay.get(header)))
                    except Exception as e:
                        print('c', e)
                        pass
                print('Config loading successful.')
        except:
            pass

    def control_textEdit_expectedPiList(self):
        global Expected_IDs

        Expected_IDs = GUI.control_textEdit_expectedPiList.toPlainText().replace('\n', ',').replace(' ', '').replace(
            ',,,', ',').replace(',,', ',').strip(',').split(',')

        try:
            with open('Host_config/expected_ids.pkl', 'wb') as f:
                pickle.dump(Expected_IDs, f)
        except:
            pass


    def enCapture(self):
        GUI.control_pushButton_capture.setEnabled(False)
        time.sleep(10)
        GUI.control_pushButton_capture.setEnabled(True)


    def control_pushButton_capture(self):
        global Table_updater, Capture_now

        threading.Thread(target=self.enCapture, daemon=True, args=[]).start()

        try:
            f = open("Host_config/capture_count.txt", "r")
            contents = f.readlines()
            f.close()
            cp = int(contents[0].replace('\n', '').replace(' ', ''))
        except:
            cp = 0

        cc = cp + 1
        f = open("Host_config/capture_count.txt", "w")
        f.write(str(cc))
        f.close()

        for th in Threads:
            try:
                th.lastCap = ''
                th.capStatNorm = ''
                th.capStatProj = ''
            except:
                pass
        Table_updater = True

        Capture_now = True

        data = 'capture=' + str(cc)
        for th in Threads:
            try:
                th.newData(data)
            except:
                print('Sending failed.................')
                pass



    def control_pushButton_camReboot(self):
        data = 'restartCam'
        for th in Threads:
            try:
                th.newData(data)
            except:
                print('Sending failed.... cs')
                pass


    def control_pushButton_camStop(self):
        global Threads

        data = 'stopCam'
        for th in Threads:
            try:
                th.newData(data)
            except:
                print('Sending failed.... cr')
                pass


    def control_pushButton_GPIOon(self):
        global Threads

        data = 'GPIO_ON'
        for th in Threads:
            try:
                if th.piMode == 'GPIO':
                    th.newData(data)
            except:
                print('Sending failed.... cr')
                pass


    def control_pushButton_GPIOoff(self):
        global Threads

        data = 'GPIO_OFF'
        for th in Threads:
            try:
                if th.piMode == 'GPIO':
                    th.newData(data)
            except:
                print('Sending failed.... cr')
                pass


    def control_pushButton_refreshIPs(self, pingClients=True):
        global Threads, Expected_IDs

        if pingClients == True:
            data = 'x'
            for th in Threads:
                try:
                    th.newData(data)
                except:
                    print('Sending failed.................')
                    pass

        Conns = list()
        ids = list()

        for th in Threads:
            try:
                Conns.append(
                    [th.name, th.IP, th.piMode, th.camStat, th.lastCap, th.capStatNorm, th.capStatProj, th.Temperature,
                     th.CPU, th.RAM, th.DISK])
                ids.append(th.name)
            except Exception as e:
                print(e)
                pass

        for eid in Expected_IDs:
            if eid not in ids and len(eid) > 0:
                Conns.append([eid, 'Not Connected', '', '', '', '', '', '', '', '', ''])

        rows = len(Conns)
        # print(Conns)

        Conns = sorted(Conns, key=itemgetter(0))

        GUI.control_tableWidget_info.setRowCount(rows)
        for n in range(len(Conns)):
            for m in range(0, len(Conns[n])):
                GUI.control_tableWidget_info.setItem(n, m, QtWidgets.QTableWidgetItem(Conns[n][m]))
                if 'Not Connected' in Conns[n][1] and (m == 0 or m == 0):
                    GUI.control_tableWidget_info.item(n, m).setBackground(QtGui.QColor(255, 150, 0))
                if 'Failed' in Conns[n][5]:
                    GUI.control_tableWidget_info.item(n, 5).setBackground(QtGui.QColor(255, 100, 0))
                if 'Failed' in Conns[n][6]:
                    GUI.control_tableWidget_info.item(n, 6).setBackground(QtGui.QColor(255, 100, 0))



    def config_pushButton_cameraConf(self):
        global Camera_configs

        conf_NP = dict()
        conf_Delay = dict()
        for i in range(1, GUI.config_tableWidget_cameraConfN.rowCount()):
            value1 = ''
            value2 = ''
            try:
                header = GUI.config_tableWidget_cameraConfN.verticalHeaderItem(i).text()
                try:
                    value1 = GUI.config_tableWidget_cameraConfN.item(i, 0).text()
                except:
                    pass
                try:
                    value2 = GUI.config_tableWidget_cameraConfP.item(i, 0).text()
                except:
                    pass
                conf_NP[header] = [value1, value2]
            except:
                pass

        for i in range(GUI.config_tableWidget_delayConf.rowCount()):
            value = ''
            try:
                header = GUI.config_tableWidget_delayConf.verticalHeaderItem(i).text()
                try:
                    value = GUI.config_tableWidget_delayConf.item(i, 0).text()
                except:
                    pass
                conf_Delay[header] = value
            except:
                pass

        Camera_configs.update({'camera': conf_NP})
        Camera_configs.update({'delay': conf_Delay})

        # print(conf_NP)
        # print(conf_Delay)
        # print(Camera_configs)

        with open('Host_config/Camera_configs.pkl', 'wb') as fp:
            pickle.dump(Camera_configs, fp)

        print('Camera configs updated.')

        for th in Threads:
            try:
                th.send_cameraConf()
            except:
                print('Sending failed.................')
                pass

        self.conf_status_update('Updating configurations ...')

    def control_pushButton_refreshSysStat(self):
        global Threads, Table_updater

        for th in Threads:
            th.Temperature = ''
            th.CPU = ''
            th.RAM = ''
            th.DISK = ''

        Table_updater = True

        data = 'systemStat'
        for th in Threads:
            try:
                th.newData(data)
            except:
                print('Sending failed.... ss')
                pass

    def config_pushButton_projectorSync(self):
        global Projector_sysc
        Projector_sysc = True
        self.conf_status_update('Synchronizing projectors ...')

    def conf_status_update(self, status):
        def up_status():
            GUI.config_label_status.setText(status)
            time.sleep(2)
            GUI.config_label_status.setText('')

        threading.Thread(target=up_status, daemon=True, args=[]).start()


    def config_pushButton_shutdownPi(self):
        global host

        if not GUI.config_checkBox_confirmReboot.isChecked():
            return

        server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        # Set a timeout so the socket does not block
        # indefinitely when trying to receive data.
        myIP = host
        server.settimeout(0.2)
        server.bind((myIP, 44444))

        message = "shutdown"
        message = message.encode()

        server.sendto(message, ('255.255.255.255', 37020))
        print("message sent!")

        GUI.config_checkBox_confirmReboot.setChecked(False)


    def config_pushButton_rebootPi(self):
        global host

        if not GUI.config_checkBox_confirmReboot.isChecked():
            return

        server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        # Set a timeout so the socket does not block
        # indefinitely when trying to receive data.
        myIP = host
        server.settimeout(0.2)
        server.bind((myIP, 44444))

        message = "reboot"
        message = message.encode()

        server.sendto(message, ('255.255.255.255', 37020))
        print("message sent!")

        GUI.config_checkBox_confirmReboot.setChecked(False)


    ##################### imran #########################

    def codeupload(self):
        global u_filename, uploadList, uCount
        upload_q.put("Starting Upload....")
        data = "upload" + "=" + u_filename.split("/")[-1] + "=" + str(os.path.getsize(u_filename))
        uCount = 0
        uploadList = list()
        for th in Threads:
            # if th.piMode != 'DSLR' and th.piMode != 'Pi-Camera':
            #     continue
            # if th.name != "155":
            #     continue
            uCount+=1
            try:
                th.newData(data)
                print(th.name, "-----Upload")
                uploadList.append(th.name)
            except:
                print('Upload failed.................')

        # while uCount!=0:
        #     time.sleep(1)
        #     print("Uploading")
        # upload_q.put("Failed List----", str(uploadList))


    def selectfile(self):
        global upload_q, u_filename
        print(" Select File")
        try:
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            u_filename, _ = QFileDialog.getOpenFileName(None, "Select file", "",
                                                      "All Files (*);;Python Files (*.py)", options=options)
            if u_filename:
                print(u_filename)
                upload_q.put(u_filename)
        except Exception as e:
            print(e, "--selct file")


    def pUpdate(self):
        global progressBarValue, progressBarValue2
        GUI.prev_progressBar.setValue(progressBarValue)
        GUI.prev_progressBar_D.setValue(progressBarValue2)
        # print(progressBarValue)

    def prev_pushButton_download(self):
        GUI.prev_pushButton_download.setEnabled(False)
        if GUI.checkBox_singleDownload.isChecked():
            threading.Thread(target=self.singleDownload, daemon=True, args=[]).start()
        else:
            threading.Thread(target=self.prev_pushButton_download1, daemon=True,args=[]).start()

    def singleDownload(self):
        print("singleDownload")
        progressBarValue2 = 0
        print(" getting list")
        try:
            for item in GUI.down_tableWidget_D.selectedItems():
                ptype = "Normal"
                if GUI.down_radioButton_projected.isChecked():
                    ptype = "Projected"
                data = 'singleDownload' + "=" + item.text() + '=' + ptype
                down_idlist = GUI.lineEdit_singleDownloadids.text()
                down_idlist = down_idlist.replace(' ', '')
                down_idlist = down_idlist.split(",")
                print(down_idlist)
                for th in Threads:
                    if th.piMode != 'DSLR' and th.piMode != 'Pi-Camera':
                        continue
                    if th.name not in down_idlist:
                        continue
                    try:
                        th.newData(data)
                        print(th.name, " --- Downloading")
                    except:
                        print('Sending failed.................')

                break
        except Exception as e:
            print(e,"---single download error")
        GUI.prev_pushButton_download.setEnabled(True)

        
    def prev_pushButton_download1(self):
        global dCount, downloadList, progressBarValue2, down_q
        progressBarValue2 = 0
        global down_status, totalImage, imgCount
        print(" getting list")
        try:
            for item in GUI.down_tableWidget_D.selectedItems():
                # shootId = GUI.prev_comboBox_count.currentText()
                data = 'download'
                downloadList = []
                shootId = item.text()
                data = data + "=" + shootId
                print(len(Threads), "-- To be downloaded----", shootId)
                imgCount = 0
                count = 0
                for th in Threads:
                    if th.piMode != 'DSLR' and th.piMode != 'Pi-Camera':
                        count += 2

                totalImage = (len(Threads) * 2) - count
                GUI.prev_label_status_D.setText("Downloading " + str(imgCount) + "/" + str(totalImage))
                try:
                    GUI.down_tableWidget_D.setItem(item.row(),item.column()+1, QtWidgets.QTableWidgetItem("Downloading"))
                except:
                    pass
                progressBarValue2 = 0
                for th in Threads:
                    if th.piMode != 'DSLR' and th.piMode != 'Pi-Camera':
                        continue
                    # if th.name == "114" or th.name == "118":
                    #     continue
                    print(th.name, " entered --", down_status)
                    try:
                        th.newData(data)
                        downloadList.append(th.name)
                        print(th.name, " --- Downloading")
                    except:
                        print('Sending failed.................')

                    # while dCount >= 50:
                    #     time.sleep(1)
                print("waiting for threads to be close")
                tTime = time.time()
                while dCount != 0 and time.time() - tTime <=150:
                    print(time.time() - tTime)
                    print("waiting.... thread to be 0", downloadList)
                    time.sleep(1)
                print(downloadList)
                print(len(downloadList),'----------RE---downloadList')
                for i in range(2):
                    if downloadList == []:
                        break
                    for th in Threads:
                        if th.name not in downloadList:
                            continue
                        try:
                            th.newData(data)
                            print(th.name, ' ----------RE---downloadList')
                        except:
                            print('Sending failed.................')
                        # while dCount >= 50:
                        #     time.sleep(1)
                    time.sleep(0.5)
                    tTime = time.time()
                    while dCount != 0 and time.time() - tTime <=60:
                        print(time.time() - tTime)
                        print("verifying.....", i)
                        time.sleep(1)
                tTime = time.time()
                while dCount != 0 and time.time() - tTime <=60:
                    print(time.time() - tTime)
                    print("verifying.....2")
                    time.sleep(1)

                print(downloadList)
                print(len(downloadList),'----------RE---downloadList')

                GUI.prev_label_status_D.setText(str(downloadList)+"----Error List")
                down_q.put(str(datetime.datetime.now())+ " - " + shootId +" - "+ str(downloadList))
                try:
                    GUI.down_tableWidget_D.setItem(item.row(),item.column()+1, QtWidgets.QTableWidgetItem("Finished"))
                except:
                    pass
                print("Finishhhhhhhhhhh")
                
        except Exception as e:
            print(e, " getting list error")
        GUI.prev_label_status_D.setText("Download")
        GUI.prev_pushButton_download.setEnabled(True)
        progressBarValue2 = 0
    def showText(self):
        global down_q, upload_q
        if not down_q.empty():
            try:
                GUI.down_textEdit.append(down_q.get())
            except Exception as e:
                print(e,"---- down_q")

        if not upload_q.empty():
            try:
                GUI.textEdit_codeupload.append(upload_q.get())
            except Exception as e:
                print(e,"---- upload_q")

    def prev_pushButton_preview(self):
        global totalImage, imgCount
        global progressBarValue
        progressBarValue = 0
        prev_idlist = GUI.prev_lineEdit_ids.text()
        prev_idlist = prev_idlist.replace(' ', '')
        try:
            with open("Host_config/prev_idlist.txt", "w", encoding="utf-8") as f:
                f.write(prev_idlist)
        except:
            pass
        prev_idlist = prev_idlist.split(",")
        print(prev_idlist)
        for i in range(len(imgShowList)):
            imgShowList[i] = ""
        for i in range(len(imgShow)):
            imgShow[i] = True
        data = 'preview'
        picType = "Normal"
        if GUI.prev_radioButton_normal.isChecked():
            picType = "Normal"
        else:
            picType = "Projected"
        shootId = GUI.prev_comboBox_count.currentText()
        data = data + "=" + shootId + '=' + picType
        global imgTab
        for i in range(len(imgTab)):
            imgTab[i] = 0

        imgCount = 0
        totalImage = len(prev_idlist)
        GUI.prev_label_status.setText("Preview " + str(imgCount) + "/" + str(totalImage))
        for th in Threads:
            if th.piMode != 'DSLR' and th.piMode != 'Pi-Camera':
                continue
            if th.name in prev_idlist:
                try:
                    GUI.prev_pushButton_preview.setEnabled(False)
                    th.newData(data)
                    print(th.name, "-----Preview")
                except:
                    print('Sending failed.................')
                    GUI.prev_pushButton_preview.setEnabled(True)
                    pass
        GUI.prev_pushButton_preview.setEnabled(True)

    def show_image(self):
        global imgShow, imgShowList, imgTab
        try:
            if imgShow[0] == True:
                scene = Qt.QGraphicsScene()
                scene.addPixmap(Qt.QPixmap(imgShowList[0]))
                GUI.prev_graphicsView_1.setScene(scene)
                GUI.prev_graphicsView_1.show()
                imgShow[0] = False
            if imgShow[1] == True:
                scene = Qt.QGraphicsScene()
                scene.addPixmap(Qt.QPixmap(imgShowList[1]))
                GUI.prev_graphicsView_2.setScene(scene)
                GUI.prev_graphicsView_2.show()
                imgShow[1] = False
            if imgShow[2] == True:
                scene = Qt.QGraphicsScene()
                scene.addPixmap(Qt.QPixmap(imgShowList[2]))
                GUI.prev_graphicsView_3.setScene(scene)
                GUI.prev_graphicsView_3.show()
                imgShow[2] = False
            if imgShow[3] == True:
                scene = Qt.QGraphicsScene()
                scene.addPixmap(Qt.QPixmap(imgShowList[3]))
                GUI.prev_graphicsView_4.setScene(scene)
                GUI.prev_graphicsView_4.show()
                imgShow[3] = False
            if imgShow[4] == True:
                scene = Qt.QGraphicsScene()
                scene.addPixmap(Qt.QPixmap(imgShowList[4]))
                GUI.prev_graphicsView_5.setScene(scene)
                GUI.prev_graphicsView_5.show()
                imgShow[4] = False
            if imgShow[5] == True:
                scene = Qt.QGraphicsScene()
                scene.addPixmap(Qt.QPixmap(imgShowList[5]))
                GUI.prev_graphicsView_6.setScene(scene)
                GUI.prev_graphicsView_6.show()
                imgShow[5] = False
        except Exception as e:
            for i in range(len(imgShow)):
                imgShow[i] = False
            print(e)

    def tabCheck(self):
        # global tabActivity, tabCount
        # currentIndex = GUI.tabWidget.currentIndex()
        # tabActivity.append(currentIndex)
        # tabCount += 1
        # if tabCount == 1000:
        #     tabActivity = tabActivity[995:1000]
        #     tabCount = 0
        # if currentIndex == 2 and (tabActivity[len(tabActivity) - 2] == 0 or tabActivity[len(tabActivity) - 2] == 1):
        print("get shoot list")
        try:
            data = 'getShootList'
            for th in Threads:

                if th.piMode != 'DSLR' and th.piMode != 'Pi-Camera':
                    continue
                try:
                    th.newData(data)
                    print(th.name, ' ----  get shoot list')
                    break
                except:
                    print('Sending failed.................')
                    pass
        except:
            pass

    def prev_pushButton_delete(self):
        GUI.prev_pushButton_delete.setEnabled(False)
        try:
            data = 'deleteAllImages'
            if GUI.prev_checkBox_confirmDelete.isChecked():

                GUI.prev_checkBox_confirmDelete.setChecked(False)

                for th in Threads:
                    if th.piMode != 'DSLR' and th.piMode != 'Pi-Camera':
                        continue
                    try:
                        th.newData(data)
                        print(th.name, '---- Delete Command Send')
                    except:
                        print('Sending failed.................')
                        pass
        except:
            pass
        GUI.prev_comboBox_count.clear()
        GUI.prev_pushButton_delete.setEnabled(True)

    #####################################################


class ClientThread(threading.Thread):
    instances = []

    def __init__(self, client=None, cmd=None, name=None, IP=('', '')):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.Quit = False

        self.client = client
        # self.client.settimeout(10)

        self.cmd = cmd
        self.Q = queue.Queue()

        self.name = name
        self.IP = IP[0]
        self.piMode = ''
        self.camStat = ''
        self.lastCap = ''
        self.capStatNorm = ''
        self.capStatProj = ''

        self.CPU = ''
        self.RAM = ''
        self.DISK = ''
        self.Temperature = ''

        # print(self.IP, 'Just connected.')
        threading.Thread(target=self.receiver, daemon=True, args=[]).start()

    def run(self):
        try:
            while True:
                message = self.Q.get()
                self.client.settimeout(3)
                self.client.sendall(message.encode())
                self.client.settimeout(30)
                # print(message)

        except Exception as e:
            print(e)
            try:
                self.client.close()
            except:

                pass

            global Threads, down_status
            Threads.remove(self)
            self.Quit = True
            down_status = True

    def receiver(self):
        global Table_updater, down_status, imgCount, totalImage, progressBarValue, u_filename, uploadList, uCount
        while not self.Quit:
            try:
                rcv = self.client.recv(1024).decode()
                if len(rcv) == 0:
                    break

                if 'ID=' in rcv:
                    self.name = rcv.split('ID=')[-1].split('#')[0]

                if 'piMode=' in rcv:
                    self.piMode = rcv.split('piMode=')[-1].split('#')[0]

                if 'camStat=' in rcv:
                    self.camStat = rcv.split('camStat=')[-1].split('#')[0]

                if 'capStatNorm=' in rcv:
                    self.capStatNorm = rcv.split('capStatNorm=')[-1].split('#')[0].split(':')[0]
                    self.lastCap = rcv.split('capStatNorm=')[-1].split('#')[0].split(':')[-1]

                if 'capStatProj=' in rcv:
                    self.capStatProj = rcv.split('capStatProj=')[-1].split('#')[0].split(':')[0]
                    self.lastCap = rcv.split('capStatProj=')[-1].split('#')[0].split(':')[-1]

                if 'camConfig?' in rcv:
                    self.send_cameraConf()

                if 'systemStat=' in rcv:
                    stats = rcv.split('systemStat=')[-1].split('#')[0].split(':')
                    try:
                        self.Temperature = stats[0]
                        self.CPU = stats[1]
                        self.RAM = stats[2]
                        self.DISK = stats[3]
                    except:
                        pass

                ############### Imran ############

                if 'shootList=' in rcv:
                    try:
                        data = rcv.replace("shootList=", "")
                        data = data.split(",")
                        for i in range(len(data)):
                            data[i] = int(data[i])
                        data.sort(reverse=True)
                        for i in range(len(data)):
                            data[i] = str(data[i])

                        GUI.prev_comboBox_count.clear()
                        GUI.prev_comboBox_count.addItems(data)
                        threading.Thread(target=shootListUpdate, daemon=True, args=[data,]).start()
                    except Exception as e:
                        print(e, "---- Shoot List")

                ##################################

                Table_updater = True
                print(self.IP, rcv)
            except Exception as e:
                down_status = True
                # print(e, " -------This")
                pass

    def newData(self, data):
        self.Q.put(data)

    def send_cameraConf(self):
        global Camera_configs
        conf_str = json.dumps(Camera_configs)
        # conf_dic = json.loads(conf_str)
        msg = 'camConfig=' + conf_str
        self.Q.put(msg)


def shootListUpdate(data):
    try:
        GUI.down_tableWidget_D.setRowCount(len(data))
        for item, i  in zip(data,range(len(data))):
            GUI.down_tableWidget_D.setItem(int(i),0, QtWidgets.QTableWidgetItem(str(item)))
            GUI.down_tableWidget_D.setItem(int(i),1, QtWidgets.QTableWidgetItem(""))
    except Exception as e:
        print(e, " --- Table update")

class projectorThread(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.setDaemon(True)

        self.threads = []

    def run(self):
        myip = self.get_my_ip()
        myrange = myip.rsplit('.', 1)[0] + '.'
        print(myrange)

        for i in range(256):
            ip = myrange + str(i)
            port = 4352
            threading.Thread(target=self.check_socket, daemon=True, args=[ip, port]).start()

        while True:
            time.sleep(2)

    def get_my_ip(self):
        global host
        return host

        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        # print(ip)
        return ip

    def check_socket(self, host, port):
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            sock.settimeout(2)
            if sock.connect_ex((host, port)) == 0:
                print("Projector found =", host)
                self.projectorController(host)

    def confirm_mute(self, projector):
        a, b = projector.get_mute()
        if not b:
            print('Muting forcely.......')
            projector.set('AVMT', '31')

        time.sleep(1)
        print(projector.get_mute())

    def projectorController(self, IP):
        global Capture_now, Camera_configs, All_projectors, Projector_sysc

        projector = Projector.from_address(IP)
        projector.authenticate()
        print('Projector successfully authenticated.', IP)

        projector.set_power('on')
        for ii in range(5):
            time.sleep(2)
            pr = projector.get_power()
            print(IP, pr)
            if pr == 'on':
                time.sleep(0.5)
                break

        # projector.set('AVMT', '31')
        # print(projector.get_mute())
        self.confirm_mute(projector)

        All_projectors.append(IP)

        while True:
            time.sleep(0.002)

            if Capture_now == True:
                print('Projector...', IP)

                d1 = float(Camera_configs.get('delay').get('projection_on').strip())
                d2 = float(Camera_configs.get('delay').get('projection_off').strip())

                time.sleep(d1)
                # print('1', IP, projector.get_mute())
                projector.set('AVMT', '30')
                print('unmuted............', IP)

                time.sleep(d2)
                # print('2', IP, projector.get_mute())
                projector.set('AVMT', '31')
                print('muted..........', IP)

                # time.sleep(1)
                print('All done -->', IP, projector.get_mute())
                Capture_now = False

            if Projector_sysc == True:
                self.confirm_mute(projector)
                # confirm mute has delay, so delay here is not required.
                Projector_sysc = False


class ImranThread(threading.Thread):
    instances = []

    def __init__(self, client=None, cmd=None, name=None, IP=('', '')):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.Quit = False
        self.client = client
        self.client.settimeout(10)
        self.Q = queue.Queue()
        self.IP = IP[0]
        # print(self.IP, 'Just connected.')
        

    def run(self):
        global Table_updater, down_status, imgCount, totalImage, progressBarValue, dCount, host, progressBarValue2
        global downloadList, uCount, upload_q, u_filename, down_q
        try:
            print("receiving......")
            rcv = self.client.recv(1024).decode()
            global dCount
            print(rcv)
            ############### Imran ############
            if 'imgSizeSingle=' in rcv:
                try:
                    rcv = rcv.replace("imgSizeSingle=", "")
                    blockSize = int(rcv.split("=")[0])
                    filename = rcv.split("=")[2]
                    port = 6000 + int(rcv.split("=")[1])

                    sp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sp.bind((host, port))
                    sp.listen(5)

                    client, addr = sp.accept()

                    temp = []
                    print("Block size ---", blockSize)
                    size = 0
                    GUI.prev_label_status_D.setText("Downloading " + rcv.split("=")[1])
                    time.sleep(0.5)
                    chunk = client.recv(blockSize)
                    temp.append(chunk)
                    size = len(chunk)
                    while chunk:
                        try:
                            chunk = client.recv(blockSize)
                            
                            if size == blockSize or chunk == 'done'.encode():
                                print("received done")
                                down_q.put("Single Donwload Status for " + rcv.split("=")[1] + " - Success " + filename)
                                break
                            size += len(chunk)
                            progressBarValue2 = int((size / blockSize) * 100)
                            temp.append(chunk)
                            print(size, "---chunk")
                        except:
                            down_q.put("Single Donwload Status for " + rcv.split("=")[1] + " - Failed " + filename)
                            pass
                    else:
                        print("chunk zero single download")
                        down_q.put("Single Donwload Status for " + rcv.split("=")[1] + " - Failed " + filename)

                    
                    data = b''.join(temp)
                    del temp
                    print(len(data), " ---final data")
                    with open(filename, 'wb') as f:
                        f.write(data)
                    print("finish")

                except Exception as e:
                    down_q.put("Single Donwload Status for " + rcv.split("=")[1] + " - Failed at " + str(size))
                    print(e, "----singleDownload")


            if "uploadReady" in rcv:
                print('uploadReady')
                try:
                    rcv = rcv.replace("uploadReady=", "")
                    port = 8000 + int(rcv)
                    sp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sp.bind((host, port))
                    sp.listen(5)

                    client, addr = sp.accept()
                    
                    with open(u_filename, "r") as f:
                        while True:
                            data = f.read(1024)
                            print(len(data), "--- chunk sent")
                            if not data:
                                time.sleep(0.5)
                                client.sendall("done".encode())
                                break
                            client.sendall(data.encode())
                        time.sleep(0.5)
                        data = client.recv(1024).decode()
                        if data == 'done':
                            # uploadList.remove(self.name)
                            upload_q.put("Done----", str(port))
                            uCount-=1
                except Exception as e:
                    print(e,"---- file upload")
                    uCount-=1    

            if 'imgSize=' in rcv:
                try:
                    rcv = rcv.replace("imgSize=", "")
                    blockSize = int(rcv.split("=")[0])
                    filename = rcv.split("=")[1]
                    port = 6000 + int(rcv.split("=")[2])

                    sp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sp.bind((host, port))
                    sp.listen(5)

                    client, addr = sp.accept()

                    chunk = client.recv(blockSize)
                    temp = []
                    temp.append(chunk)
                    size = len(chunk)
                    print("Block size ---", blockSize)
                    while chunk:
                        try:
                            chunk = client.recv(blockSize)
                            size += len(chunk)
                            temp.append(chunk)
                            print(len(chunk), "---chunk")
                            if size == blockSize:
                                break
                        except:
                            pass
                    else:
                        GUI.prev_pushButton_preview.setEnabled(True)

                    size = 0
                    data = b''.join(temp)
                    del temp
                    print(len(data), " ---final data")
                    filename = "Preview/" + filename
                    with open(filename, 'wb') as f:
                        f.write(data)
                    print("finish")
                    img = Image.open(filename)
                    new_width = 340
                    new_height = 250
                    img = img.resize((new_width, new_height), Image.ANTIALIAS)
                    img.save(filename)
                    imgCount += 1
                    GUI.prev_label_status.setText("Preview " + str(imgCount) + "/" + str(totalImage))
                    progressBarValue = int((imgCount / totalImage) * 100)
                    print(progressBarValue, imgCount, totalImage)
                    for i in range(len(imgTab)):
                        if imgTab[i] == 0:
                            imgShowList[i] = filename
                            imgTab[i] = 1
                            imgShow[i] = True
                            break

                except Exception as e:
                    GUI.prev_label_status.setText("Failed")
                    print(e)

            try:
                    sp.close()
            except:
                pass
            if 'imgdSize=' in rcv:
                try:
                    dCount+=1
                    rcv = rcv.replace("imgdSize=", "")
                    blockSize = int(rcv.split("=")[0])
                    print(blockSize)
                    dShootId = rcv.split("=")[1]
                    filename = rcv.split("=")[2]
                    tData = filename.split("/")
                    # print(tData)
                    dId = filename.split("/")[-1]
                    port = 7000 + int(dId.replace(".jpg",""))
                    # print(port)
                    sp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sp.bind((host, port))
                    sp.listen(5)

                    client, addr = sp.accept()

                    GUI.prev_label_status_D.setText("Downloading " + str(imgCount) + "/" + str(totalImage) + " " + dId)
                    try:
                        if os.path.exists(tData[0] + '/' + tData[1]) != True:
                            os.mkdir(tData[0] + '/' + tData[1])
                        if os.path.exists(tData[0] + '/' + tData[1] + '/' + tData[2]) != True:
                            os.mkdir(tData[0] + '/' + tData[1] + '/' + tData[2])
                    except Exception as e:
                        print(e, " Making of Dir---", tData[0] + '/' + tData[1])
                    chunk = client.recv(blockSize)
                    temp = []
                    temp.append(chunk)
                    size = len(chunk)
                    # print(size, " first chunk")
                    while chunk:
                        try:
                            chunk = client.recv(blockSize)
                            size += len(chunk)
                            # print(size)
                            temp.append(chunk)
                            if size == blockSize or "done".encode() in chunk:
                                # print("Done")
                                break
                        except:
                            down_status = True
                            print('exc')
                    else:
                        print('chunk - 0  ---',dId)
                    data = b''.join(temp)
                    del temp
                    # print(len(data), " ---final data")
                    if size == blockSize:
                        with open(filename, 'wb') as f:
                            f.write(data)
                        print(filename, ' ---- Done')
                        imgCount += 1
                        GUI.prev_label_status_D.setText("Downloading " + str(imgCount) + "/" + str(totalImage) + " " + dId)
                        progressBarValue2 = int((imgCount / totalImage) * 100)
                        print(progressBarValue2)
                        if "Projected" in filename:
                            downloadList.remove(dId.replace(".jpg",""))
                    dCount-=1
                except Exception as e:
                    print('Download error --')
                    print(str(e))
                    dCount-=1
                    pass
                try:
                    sp.close()
                except:
                    pass
            ##################################
        except Exception as e:
            print(e, " ------- Preview and Download")
            pass


def socket_main():
    global Threads, host
    print("Server starting...")

    # host = '192.168.2.10'
    # host = '192.168.0.100'
    port = 5001

    if MyOS == 'windows':
        host = socket.gethostname()
        # host = '192.168.0.101'

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, port))
    s.listen(5)

    print('done')

    while True:
        try:
            c, addr = s.accept()
            th = ClientThread(client=c, IP=addr)
            th.start()
            Threads.append(th)
        except Exception as e:
            print("Main error =", e)


def socket_imran():
    global host
    print("Server starting...")

    # host = '192.168.2.10'
    # host = '192.168.0.100'
    # host = "localhost"
    port = 5002

    if MyOS == 'windows':
        host = socket.gethostname()
        # host = '192.168.0.101'

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, port))
    s.listen(5)

    print('done')

    while True:
        try:
            c, addr = s.accept()
            th = ImranThread(client=c, IP=addr)
            th.start()
        except Exception as e:
            print("Imran error =", e)


if __name__ == '__main__':
    threading.Thread(target=socket_main, daemon=True, args=[]).start()
    threading.Thread(target=socket_imran, daemon=True, args=[]).start()
    projectorThread().start()

    app = QtWidgets.QApplication(sys.argv)
    dialog = QtWidgets.QDialog()

    try:
        def resource_path(relative_path):
            if hasattr(sys, '_MEIPASS'):
                return os.path.join(sys._MEIPASS, relative_path)
            return os.path.join(os.path.abspath("."), relative_path)

        p = resource_path('My_Files\icon.ico')
        dialog.setWindowIcon(QtGui.QIcon(p))
    except:
        pass

    dialog.setWindowFlags(dialog.windowFlags() |
                          QtCore.Qt.WindowMinimizeButtonHint |
                          QtCore.Qt.WindowSystemMenuHint)
    dialog.setWindowFlags(dialog.windowFlags() |
                          QtCore.Qt.WindowSystemMenuHint |
                          QtCore.Qt.WindowMinMaxButtonsHint)

    GUI = MyGui(dialog)
    dialog.show()

    myMC = myMainClass()

    app.exec_()
    sys.exit()







