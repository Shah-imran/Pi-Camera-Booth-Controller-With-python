import socket, os

def Shutdown():
   os.system("sudo shutdown -h now")
def Restart():
   os.system("sudo shutdown -r now")


client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
client.bind(("", 37020))
while True:
    data, addr = client.recvfrom(1024)

    data = data.decode()
    print("received message: %s"%data)
    # if 'reboot' in data:
    #     Restart()
    # if 'shutdown' in data:
    #     Shutdown()




