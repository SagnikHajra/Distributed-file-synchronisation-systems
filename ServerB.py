#!/usr/bin/python3
'''
Name: Sagnik Hajra
ID: 1001851338
'''
from SocketClass import SocketClass


# ServerB inherits SocketClass
# Create a socket and the listen for any client, once a connection is established with a client, communicate with it.
class ServerB(SocketClass):
    def __init__(self):
        self.ADD = ''
        self.PRT = 9001
        self.parallel_server_port = 8001
        self.file_excng_server_port = 6001
        self.file_excng_client_port = 5001
        self.workingDir = "C:/Users/Sagnik Hajra/Documents/serverb"

        super(ServerB, self).__init__(self.ADD, self.PRT, server=True, clientLimit=3)


if __name__ == "__main__":
    # let the game begin
    s = ServerB()
    s.start()