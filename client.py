#!/usr/bin/python3

'''
Name: Sagnik Hajra
ID: 1001851338
'''
from SocketClass import SocketClass

socket = SocketClass('localhost', 9001)


def print_the_message(serverMsg):
    serverMsg = serverMsg.strip().split("\n")

    for i in range(len(serverMsg)):
        if not serverMsg[i].strip():
            serverMsg[i] = []
        else:
            serverMsg[i] = serverMsg[i].split("||")

    serverMsg = sorted(serverMsg, key=lambda item: item[3])
    print("file/dir names:")
    for item in serverMsg:
        if item:
            print("\t".join(item))


while True:
    serverMsg = socket.receive(socket.socket)
    if serverMsg == socket.CONNECTION_CLOSE:
        break
    elif serverMsg in socket.messages:
        print(socket.messages[serverMsg])
    elif serverMsg not in socket.messages:
        print_the_message(serverMsg)
    clientData = input("\ncommand: ")
    clientData = clientData.strip()
    socket.send(clientData, socket.socket)

print("Closing the client socket")
socket.socket.close()
