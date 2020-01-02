# Socket client example in python
# https://picamera.readthedocs.io/en/release-1.10/api_camera.html#picamera.camera.PiCamera.shutter_speed

# 'https://dl.dropboxusercontent.com/s/knrgxzguvtbd3kc/client_pi.py?dl=0'

# 5/16/2019

import socket, pickle, threading
import sys, time, os
import platform, subprocess
import json, psutil
from subprocess import PIPE, Popen
import shlex, shutil
from PIL import Image
import piexif


MyOS = platform.system().lower()
print(MyOS)

global host

host = "192.168.2.10"

if MyOS != 'windows':
    import picamera
    import RPi.GPIO as GPIO
    from sendfile import sendfile
    # import cv2 as cv
    # import numpy as np

FOLDER = '/home/pi/Desktop/'
if MyOS == 'windows':
    FOLDER = ''

MyID = 'None'
try:
    f = open(FOLDER + "ID.txt", "r")
    contents = f.readlines()
    f.close()
    MyID = contents[0].replace(' ','').replace('\n','')
except:
    pass

######### Imran #############
global imageDir

imageDir = FOLDER + 'Client_Image_Album'
#############################


Camera_mode = ''
Camera = None
Camera_configs = dict()


def Main():
    global Camera_configs, Camera_mode, host

    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(10)
            print('Socket Created')

            # host = '192.168.2.10'
            # host = "localhost"
            port = 5001

            if MyOS == 'windows':
                host = socket.gethostname()

            t = time.time()
            s.connect((host, port))
            print("Connected.")

            try:
                message = "#ID=" + str(MyID)
                s.sendall(message.encode())
            except Exception as e:
                print(e)

            Camera_mode = detect_cameraMode()
            msg = '#piMode=' + Camera_mode
            s.sendall(msg.encode())

            msg = '#camConfig?'
            s.sendall(msg.encode())

            while True:
                rcv = s.recv(1024)
                rcv = rcv.decode()
                print(rcv)

                if len(rcv) == 0:
                    print('Trying reconnect')
                    break

                if 'capture=' in rcv:
                    try:
                        shutil.rmtree(FOLDER + 'img_tmp')
                    except:
                        pass

                    image_count = rcv.split('=')[-1].replace('x','')
                    camera_capture(image_count, sock=s)

                if 'restartCam' in rcv:
                    msg = '#camConfig?'
                    s.sendall(msg.encode())


                if 'stopCam' in rcv:
                    msg = stop_pycam()
                    msg = '#camStat=' + msg
                    s.sendall(msg.encode())

                if 'GPIO_ON' in rcv and Camera_mode == "GPIO":
                    GPIO.output(17, GPIO.HIGH)
                    msg = '#camStat=GPIO On'
                    s.sendall(msg.encode())

                if 'GPIO_OFF' in rcv and Camera_mode == "GPIO":
                    GPIO.output(17, GPIO.LOW)
                    msg = '#camStat=GPIO Off'
                    s.sendall(msg.encode())


                if 'camConfig=' in rcv:

                    try:
                        shutil.rmtree(FOLDER + 'img_tmp')
                    except:
                        pass

                    msg = stop_pycam()
                    msg = '#camStat=' + msg
                    s.sendall(msg.encode())

                    conf_str = rcv.split('camConfig=', 1)[-1]
                    Camera_configs = json.loads(conf_str)
                    msg = '#camStat=' + 'Config-Loaded'
                    s.sendall(msg.encode())

                    Camera_mode = detect_cameraMode()
                    msg = '#piMode=' + Camera_mode
                    s.sendall(msg.encode())

                    if Camera_mode == 'Pi-Camera':
                        msg = init_piCam()
                        msg = '#camStat=' + msg
                        s.sendall(msg.encode())

                    if Camera_mode == 'DSLR':
                        try:
                            # output = subprocess.Popen(['gphoto2', '--set-config capturetarget=1'],
                            #                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                            # stdout, stderr = output.communicate()
                            output = subprocess.check_output("sudo gphoto2 --set-config capturetarget=1", shell=True)
                        except:
                            pass

                if 'systemStat' in rcv:
                    msg = get_system_state()
                    msg = '#systemStat=' + msg
                    s.sendall(msg.encode())



                ############## imran ##################

                if 'deleteAllImages' in rcv:
                    try:
                        print("Starting deleting Procedure")
                        folderList = os.listdir(imageDir)
                        for item in folderList:
                            shutil.rmtree(imageDir + "/" + item)
                        print('directory deleted')
                    except Exception as e:
                        print(e, "------------------- Directory delete error")

                if 'getShootList' in rcv:
                    shootList = os.listdir(imageDir)
                    msg = "shootList="
                    for i in shootList:
                        msg = msg + i + ","
                    msg = msg[:-1]
                    s.sendall(msg.encode())

                if 'upload' in rcv:
                    print("upload")
                    threading.Thread(target=upload, args=[rcv,]).start()
                    
                if 'singleDownload' in rcv:
                    print("singleDownload")
                    threading.Thread(target=singleDownload, args=[rcv,]).start()

                if 'preview' in rcv:
                    print("preview")
                    threading.Thread(target=preview, args=[rcv,]).start()

                if 'download=' in rcv:
                    print("download")
                    threading.Thread(target=download, args=[rcv,]).start()

        except Exception as e:
            print('Reconnecting...', e)
            time.sleep(3)
            pass

def singleDownload(rcv):
    global host
    try:
        sTemp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sTemp.settimeout(10)
        print('Socket Created')

        # host = "localhost"
        port = 5002
        sTemp.connect((host, port))
        print("Connected.")

        rcv = rcv.replace("singleDownload=", "")
        shootId = rcv.split("=")[0]
        picType = rcv.split("=")[1]

        imgFileName = imageDir + "/" + shootId + "/" + picType+ "/"
        imgs = os.listdir(imgFileName)
        imgFileName += imgs[0]
        imgfile = open(imgFileName, "rb")
        blocksize = os.path.getsize(imgFileName)
        print(blocksize)
        offset = 0
        
        msg1 = "Download/" + shootId + "/" + picType + "/" + MyID + ".jpg"
        msg = "imgSizeSingle=" + str(blocksize) + '=' + MyID + '=' + msg1
        print(msg)
        sTemp.sendall(msg.encode())
        time.sleep(1)

        sp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sp.settimeout(10)
        print('Socket Created')

        # host = "localhost"
        port = 6000 + int(MyID)
        sp.connect((host, port))
        print("Connected.")
        size = 0
        while True:
            data = imgfile.read(4096)
            size = size + len(data)            
            if not data:
                time.sleep(0.5)
                sp.sendall("done".encode())
                break
            sp.sendall(data)
            print(size, "--- chunk sent")

    except Exception as e:
        print(e, '----Single Download sending error')
    finally:
        try:
            sTemp.close()
            sp.close()
            imgfile.close()
        except:
            pass

def preview(rcv):
    global host
    try:
        sTemp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sTemp.settimeout(10)
        print('Socket Created')

        # host = "localhost"
        port = 5002
        sTemp.connect((host, port))
        print("Connected.")

        rcv = rcv.replace("preview=", "")
        shootId = rcv.split("=")[0]
        picType = rcv.split("=")[1]
        imgFileName = imageDir + "/" + shootId + "/" + picType+ "/"
        imgs = os.listdir(imgFileName)
        imgFileName += imgs[0]

        # ########### Farhan (image resize) #############
        try:
            os.remove(FOLDER + imgs[0])
            time.sleep(0.1)
        except:
            pass
        basewidth = 640
        img = Image.open(imgFileName)
        wpercent = (basewidth / float(img.size[0]))
        hsize = int((float(img.size[1]) * float(wpercent)))
        img = img.resize((basewidth, hsize), Image.ANTIALIAS)
        imgFileName = FOLDER + imgs[0]
        img.save(imgFileName)
        time.sleep(0.1)
        # ##############################################

        imgfile = open(imgFileName, "rb")
        blocksize = os.path.getsize(imgFileName)
        print(blocksize)
        offset = 0
        msg = "imgSize=" + str(blocksize) + '=' + imgs[0] + "=" + MyID
        print(msg)
        sTemp.sendall(msg.encode())
        time.sleep(1)

        sp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sp.settimeout(10)
        print('Socket Created')

        # host = "localhost"
        port = 6000 + int(MyID)
        sp.connect((host, port))
        print("Connected.")

        while True:
            time.sleep(0.5)
            sent = sendfile(sp.fileno(), imgfile.fileno(), offset, blocksize)

            offset += sent
            print(sent, "sent amount")
            if sent == 0:
                break  # EOF

    except Exception as e:
        print(e, '----image preview sending error')
    finally:
        try:
            sTemp.close()
            sp.close()
            imgfile.close()
        except:
            pass


def upload(rcv):
    global host
    try:
        rcv = rcv.replace('upload=','')
        blocksize = int(rcv.split('=')[-1])
        filename = rcv.split('=')[-2]
        filename = FOLDER + filename
        sTemp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sTemp.settimeout(10)
        print('Socket Created')

        port = 5002
        sTemp.connect((host, port))
        print("Connected.")
        msg = 'uploadReady' + "=" + MyID
        msg = msg.encode()
        sTemp.sendall(msg)

        
        time.sleep(1)

        sp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sp.settimeout(10)
        print('Socket Created')

        # host = "localhost"
        port = 8000 + int(MyID)
        sp.connect((host, port))
        print("Connected.")
        temp = []
        try:
            if os.path.isfile(filename):
                os.remove(filename)
            else:
                pass
        except Exception as e:
            print(e, "--- error while removing file")
        while True:
            data = sp.recv(blocksize)
            print(len(data.decode()), "---data chunk received")
            if data == ''.encode() or data == "done".encode():
                break
            temp.append(data.decode())
        print("here")

        data = ''.join(temp)
        if data:
            with open(filename, "w") as f:
                f.write(data)
            print("file saved---", filename)
        else:
            print("file not saved")
        sp.sendall("done".encode())

    except Exception as e:
        print(e, "--- upload error")
    finally:
        try:
            sTemp.close()
            sp.close()
        except:
            pass



def download(rcv):
    global host
    try:
        
        for item in ["Normal", "Projected"]:
            sTemp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sTemp.settimeout(10)
            print('Socket Created')

            # host ="localhost"
            port = 5002
            t = time.time()
            sTemp.connect((host, port))
            print("Connected.")
            downShootId = rcv.replace("download=", "")

            file = imageDir + "/" + downShootId + "/" + item + "/" + MyID + ".jpg"

            imgfile = open(file, "rb")
            blocksize = os.path.getsize(file)
            offset = 0
            msg = "imgdSize=" + str(blocksize) + "=" + downShootId + "="
            msg1 = "Download/" + downShootId + "/" + item + "/" + MyID + ".jpg"
            msg = msg + msg1
            sTemp.sendall(msg.encode())

            time.sleep(1)

            sp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sp.settimeout(10)
            print('Socket Created')

            # host = "localhost"
            port = 7000 + int(MyID)
            sp.connect((host, port))
            print("Connected.")
            while True:
                time.sleep(0.5)
                sent = sendfile(sp.fileno(), imgfile.fileno(), offset, blocksize)
                offset += sent
                print(sent, "sent amount")
                if sent == 0:
                    break  # EOF

            imgfile.close()
            time.sleep(0.5)
            print("Done")
            sp.sendall("done".encode())
    except Exception as e:
        print(e, "---- error while sending")
    finally:
        try:
            sTemp.close()
            sp.close()
            imgfile.close()
        except:
            pass


def config_picam(mode=0):
    global Camera_configs
    try:
        if MyOS == 'windows':
            time.sleep(0.05)
            if mode == 0:
                return 'Normal Configed'
            if mode == 1:
                return 'Projected Configed'

        ### mode: 0 = Normal; 1 = Projected
        camSet = Camera_configs.get('camera')

        try:
            Camera.resolution = (Camera.MAX_RESOLUTION)
            Camera.framerate = 15
        except:
            print("This config not loaded.")
        try:
            d = int(camSet.get('Sharpness')[mode])
            Camera.sharpness = d
        except:
            print("This config not loaded.")
        try:
            d = int(camSet.get('Contrast')[mode])
            Camera.contrast = d
        except:
            print("This config not loaded.")
        try:
            d = int(camSet.get('Brightness')[mode])
            Camera.brightness = d
        except:
            print("This config not loaded.")
        try:
            d = int(camSet.get('ISO')[mode])
            Camera.iso = d
        except:
            print("This config not loaded.")
        try:
            d = int(camSet.get('EV')[mode])
            Camera.exposure_compensation = d
        except:
            print("This config not loaded.")
        try:
            d = int(camSet.get('Rotation')[mode])
            Camera.rotation = d
        except:
            print("This config not loaded.")
        try:
            d = int(camSet.get('Shutter_Speed')[mode])
            Camera.shutter_speed = d
        except:
            print("This config not loaded.")
        try:
            d = camSet.get('DRC')[mode]
            Camera.drc_strength = d
        except:
            print("This config not loaded.")
        try:
            d = camSet.get('AWB')[mode]
            Camera.awb_mode = d
        except:
            print("This config not loaded.")
        try:
            aa = camSet.get('AWBG')[mode].replace('(', '').replace(')', '')
            al = float(aa.split(',')[0])
            ar = float(aa.split(',')[-1])
            Camera.awb_gains = (al, ar)  # (1.0,1.0)
        except:
            print("This config not loaded.")
        try:
            d = int(camSet.get('Saturation')[mode])
            Camera.saturation = d
        except:
            print("This config not loaded.")


        if mode == 0:
            return 'Normal Configed'
        if mode == 1:
            return 'Projected Configed'

    except Exception as e:
        print('Config loading failed =', e)
        return 'Config Failed'



def init_piCam():
    global Camera
    try:
        if MyOS == 'windows':
            time.sleep(1)
            return 'Initialized win'

        Camera = picamera.PiCamera()

        return 'Initialized'
    except:
        return 'Failed'


def stop_pycam():
    global Camera
    try:
        if MyOS == 'windows':
            time.sleep(1)
            return 'stopped win'

        Camera.close()
        return 'stopped'
    except:
        return '----'


def camera_capture(image_count, sock=None):
    global Camera_mode, Camera_configs, FOLDER, MyID
    # https://picamera.readthedocs.io/en/release-1.10/api_camera.html

    try:
        os.makedirs(FOLDER + 'Client_Image_Album/' + str(image_count) + '/Normal')
        os.makedirs(FOLDER + 'Client_Image_Album/' + str(image_count) + '/Projected')
    except Exception as e:
        print(e)
        pass

    if Camera_mode == 'GPIO':
        delaySet = Camera_configs.get('delay')
        ### 1
        try:
            delay = float(delaySet.get('GPIO_delay_1').replace(' ', ''))
            time.sleep(delay)
            g_state = delaySet.get('GPIO_state_1').replace(' ', '').lower()
            if 'on' in g_state:
                GPIO.output(17, GPIO.HIGH)
                send_status('#camStat=GPIO ON', sock)
            elif 'off' in g_state:
                GPIO.output(17, GPIO.LOW)
                send_status('#camStat=GPIO OFF', sock)
        except:
            send_status('#camStat=Error', sock)
        ## 2
        try:
            delay = float(delaySet.get('GPIO_delay_2').replace(' ', ''))
            time.sleep(delay)
            g_state = delaySet.get('GPIO_state_2').replace(' ', '').lower()
            if 'on' in g_state:
                GPIO.output(17, GPIO.HIGH)
                send_status('#camStat=GPIO ON', sock)
            elif 'off' in g_state:
                GPIO.output(17, GPIO.LOW)
                send_status('#camStat=GPIO OFF', sock)
        except:
            send_status('#camStat=Error', sock)
        ## 3
        try:
            delay = float(delaySet.get('GPIO_delay_3').replace(' ', ''))
            time.sleep(delay)
            g_state = delaySet.get('GPIO_state_3').replace(' ', '').lower()
            if 'on' in g_state:
                GPIO.output(17, GPIO.HIGH)
                send_status('#camStat=GPIO ON', sock)
            elif 'off' in g_state:
                GPIO.output(17, GPIO.LOW)
                send_status('#camStat=GPIO OFF', sock)
        except:
            send_status('#camStat=Error', sock)
        ## 4
        try:
            delay = float(delaySet.get('GPIO_delay_4').replace(' ', ''))
            time.sleep(delay)
            g_state = delaySet.get('GPIO_state_4').replace(' ', '').lower()
            if 'on' in g_state:
                GPIO.output(17, GPIO.HIGH)
                send_status('#camStat=GPIO ON', sock)
            elif 'off' in g_state:
                GPIO.output(17, GPIO.LOW)
                send_status('#camStat=GPIO OFF', sock)
        except:
            send_status('#camStat=Error', sock)

    if Camera_mode == 'DSLR':
        dslr_capture(image_count, sock=sock)

    if Camera_mode == 'Pi-Camera':
        capture_picamera(image_count, sock=sock)


    colorCorrection = str(Camera_configs.get('colorCorrection'))

    if (Camera_mode == 'DSLR' or Camera_mode == 'Pi-Camera') and colorCorrection == 'True':
        try:
            camSet = Camera_configs.get('camera')

            ccf = ''
            try:
                # 'sudo cctiff -ip -q100 *profile* -ip -q100 *sRGB* -t 1 *img* *imgCC*'
                img = FOLDER + 'Client_Image_Album/' + str(image_count) + '/Normal/' + MyID + '.jpg'
                imgCC = FOLDER + 'Client_Image_Album/' + str(image_count) + '/Normal/' + MyID + 'cc.jpg'
                profile = '/home/pi/Desktop/colorcalibration/normal/' + MyID + 'profilenormal.icm'
                sRGB = '/home/pi/Desktop/colorcalibration/normal/sRGB.icm'

                argyll_normal = camSet.get('Argyll')[0]
                argyll_normal = argyll_normal.replace('*img*', img).replace('*imgCC*', imgCC)
                argyll_normal = argyll_normal.replace('*profile*', profile).replace('*sRGB*', sRGB)

                subprocess.check_output(argyll_normal, shell=True)
                send_status('#camStat=Color Corrected', sock)

                ### metadata
                piexif.transplant(img, imgCC)

                os.remove(img)
                shutil.move(imgCC, img)
            except:
                ccf = '1'
                pass

            try:
                # 'sudo cctiff -ip -q100 *profile* -ip -q100 *sRGB* -t 1 *img* *imgCC*'
                img = FOLDER + 'Client_Image_Album/' + str(image_count) + '/Projected/' + MyID + '.jpg'
                imgCC = FOLDER + 'Client_Image_Album/' + str(image_count) + '/Projected/' + MyID + 'cc.jpg'
                profile = '/home/pi/Desktop/colorcalibration/projected/' + MyID + 'profileprojected.icm'
                sRGB = '/home/pi/Desktop/colorcalibration/projected/sRGB.icm'

                argyll_projected = camSet.get('Argyll')[1]
                argyll_projected = argyll_projected.replace('*img*', img).replace('*imgCC*', imgCC)
                argyll_projected = argyll_projected.replace('*profile*', profile).replace('*sRGB*', sRGB)

                subprocess.check_output(argyll_projected, shell=True)
                send_status('#camStat=Color Corrected', sock)

                ### metadata
                piexif.transplant(img, imgCC)

                os.remove(img)
                shutil.move(imgCC, img)

            except:
                ccf += ' 2'
                pass

            if len(ccf) > 0:
                send_status('#camStat=CC Failed ' + ccf, sock)





        except:
            pass




def detect_cameraMode():
    if MyOS == 'windows':
        # return 'DSLR'
        return 'Pi-Camera'

    if os.path.isfile(FOLDER + 'GPIO.txt'):
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            GPIO.setup(17, GPIO.OUT, initial=GPIO.LOW)
            return 'GPIO'
        except:
            return 'GPIO failed'

    dslr = auto_dslr_check()
    if dslr == True:
        return 'DSLR'

    picam = auto_detect_picam()
    if picam == True:
        return 'Pi-Camera'

    return 'Nothing'


def auto_detect_picam():
    try:
        with picamera.PiCamera() as cam:
            print(cam.revision)
            print(cam.MAX_RESOLUTION)
        return True
    except:
        return False


def auto_dslr_check():
    try:
        output = subprocess.Popen(['gphoto2', '--auto-detect'],
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT)
        stdout, stderr = output.communicate()
        if "usb:" in stdout.decode():
            return True
        else:
            return False
    except Exception as e:
        print(e, "---")
        return False


def send_status(msg, sock):
    def send_stat(msg, sock):
        sock.sendall(msg.encode())

    threading.Thread(target=send_stat, daemon=True, args=[msg, sock]).start()


def capture_picamera(image_count, sock=None):
    global Camera, Camera_configs
    try:
        delaySet = Camera_configs.get('delay')

        try:
            stt = config_picam(0)
            send_status('#camStat=' + stt, sock)
            delay = float(delaySet.get('capture_picam_normal').replace(' ', ''))
            time.sleep(delay)
            send_status('#camStat=Shooting Normal', sock)
            if MyOS == 'windows':
                time.sleep(1)
                send_status('#capStatNorm=Success-win:' + image_count, sock)
            else:
                Camera.capture(FOLDER + 'Client_Image_Album/' + str(image_count) + '/Normal/' + MyID + '.jpg',
                               quality=100)
                send_status('#capStatNorm=Success:' + image_count, sock)
        except:
            send_status('#capStatNorm=Failed:' + image_count, sock)
            pass

        try:
            stt = config_picam(1)
            send_status('#camStat=' + stt, sock)
            delay = float(delaySet.get('capture_picam_projection').replace(' ', ''))
            time.sleep(delay)
            send_status('#camStat=Shooting Projected', sock)
            if MyOS == 'windows':
                time.sleep(1)
                send_status('#capStatProj=Success-win:' + image_count, sock)
            else:
                Camera.capture(FOLDER + 'Client_Image_Album/' + str(image_count) + '/Projected/' + MyID + '.jpg',
                               quality=100)
                send_status('#capStatProj=Success:' + image_count, sock)
        except:
            send_status('#capStatProj=Failed:' + image_count, sock)
            pass

        print('Image Capturing Finished.')
        send_status('#camStat=----', sock)

    except:
        print('Error...')


def dslr_capture(image_count, sock=None):
    global FOLDER, MyID

    # try:
    #     os.makedirs(FOLDER + 'img_tmp/')
    #     os.system('chmod 777 -R ' + FOLDER + 'img_tmp/')
    #     os.system('sudo chown pi:pi ' + FOLDER + 'img_tmp/')
    # except Exception as e:
    #     print(e)
    #     pass

    try:
        delaySet = Camera_configs.get('delay')
        delay = float(delaySet.get('capture_dslr_normal').replace(' ', ''))
        time.sleep(delay)
        send_status('#camStat=Shooting Normal', sock)

        if MyOS == 'windows':
            time.sleep(1)
            send_status('#capStatNorm=Success-win:' + image_count, sock)
            return

        def run_command(command):
            process = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE)
            success = 0
            for ii in range(50):
                output = process.stdout.readline()
                out = output.strip().decode()
                print(out)
                if out == '' and process.poll() is not None:
                    break
                if out:
                    if 'in location' in out:
                        success += 1
                        if success == 1:
                            send_status('#capStatNorm=Success:' + image_count, sock)
                        if success == 2:
                            send_status('#capStatProj=Success:' + image_count, sock)

            return success

        delay2 = float(delaySet.get('capture_dslr__projection').replace(' ', ''))
        # output = subprocess.check_output("gphoto2 --capture-image --frames 2 --interval " + str(delay2) + ' --force-overwrite', shell=True)
        # # print(output)
        ret = run_command("sudo gphoto2 --capture-image --frames 2 --interval " + str(delay2))
        print('returned')
        if ret == 0:
            send_status('#capStatNorm=Failed:' + image_count, sock)
            send_status('#capStatProj=Failed:' + image_count, sock)
        if ret == 1:
            send_status('#capStatProj=Failed:' + image_count, sock)

        send_status('#camStat=Downloading files', sock)

        try:
            shutil.rmtree(FOLDER + 'img_tmp')
        except:
            pass

        output = subprocess.check_output("sudo gphoto2 --get-all-files --new --force-overwrite --filename " + FOLDER + 'img_tmp/%S.%C', shell=True)
        print(output)
        send_status('#camStat=Moving files', sock)
        fileN = FOLDER + 'Client_Image_Album/' + str(image_count) + '/Normal/' + MyID + '.jpg'
        fileP = FOLDER + 'Client_Image_Album/' + str(image_count) + '/Projected/' + MyID + '.jpg'
        files = os.listdir(FOLDER + 'img_tmp/')
        print(files)

        num1 = files[-2].split('.')[0]
        suf1 = files[-2].split('.')[1]

        num2 = files[-1].split('.')[0]
        suf2 = files[-1].split('.')[1]

        if abs(int(num1.strip()) - int(num2.strip())) <= 30:
            if(int(num1.strip()) < int(num2.strip())):
                fiN = num1
                siN = suf1
                fiP = num2
                siP = suf2
            else:
                fiN = str(num2)
                siN = suf2
                fiP = str(num1)
                siP = suf1

        else:
            if (int(num1.strip()) < int(num2.strip())):
                fiN = str(num2)
                siN = suf2
                fiP = str(num1)
                siP = suf1
            else:
                fiN = num1
                siN = suf1
                fiP = num2
                siP = suf2


        nmN = fiN + '.' + siN
        nmP = fiP + '.' + siP

        shutil.move(FOLDER + 'img_tmp/' + nmN, fileN)
        shutil.move(FOLDER + 'img_tmp/' + nmP, fileP)

        try:
            send_status('#camStat=Deleting files', sock)
            for ii in range(10):
                try:
                    print('Deleting files from camera.')
                    output = subprocess.check_output("sudo gphoto2 --delete-all-files --recurse", shell=True)
                    if 'Error' not in output.decode():
                        print('breaking....')
                        break
                    time.sleep(0.5)
                except:
                    pass
        except:
            pass

        shutil.rmtree(FOLDER + 'img_tmp')

        send_status('#camStat=-----', sock)

    except:
        send_status('#capStatNorm=Failed:' + image_count, sock)
        send_status('#capStatProj=Failed:' + image_count, sock)
        pass


def get_system_state():
    def get_cpu_temperature():
        process = Popen(['vcgencmd', 'measure_temp'], stdout=PIPE)
        output, _error = process.communicate()
        return output.decode().split('=')[-1].replace('\n', '')

    cpu_temperature = ''
    cpu_usage = ''
    ram_percent_used = ''
    disk_free = ''

    try:
        cpu_temperature = str(get_cpu_temperature())
    except:
        pass
    try:
        cpu_usage = str(psutil.cpu_percent(interval=0)) + ' %'
    except:
        pass
    try:
        ram = psutil.virtual_memory()
        # ram_total = ram.total / 2 ** 20  # MiB.
        # ram_used = ram.used / 2 ** 20
        # ram_free = ram.free / 2 ** 20
        ram_percent_used = str(round(ram.percent, 2)) + ' %'
    except:
        pass
    try:
        disk = psutil.disk_usage('/')
        # disk_total = disk.total / 2 ** 30  # GiB.
        # disk_used = disk.used / 2 ** 30
        disk_free = str(round(disk.free / 2 ** 30, 2)) + ' GB'
        # disk_percent_used = disk.percent
        # print(disk_free, 'GB')
    except:
        pass

    return cpu_temperature + ':' + cpu_usage + ':' + ram_percent_used + ':' + disk_free


Main()


