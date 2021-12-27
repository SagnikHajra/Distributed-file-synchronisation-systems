#!/usr/bin/python3
'''
Name: Sagnik Hajra
ID: 1001851338

Code copied and modified
Ref: https://www.thepythoncode.com/article/send-receive-files-using-sockets-python
'''
import socket
import tqdm
import os


def receiver(working_dir, port):
    while True:
        # device's IP address
        SERVER_HOST = "127.0.0.1"
        SERVER_PORT = port
        # receive 4096 bytes each time
        BUFFER_SIZE = 4096
        SEPARATOR = "<SEPARATOR>"
        # create the server socket
        # TCP socket
        s = socket.socket()
        # bind the socket to our local address
        s.bind((SERVER_HOST, SERVER_PORT))
        # enabling our server to accept connections
        # 5 here is the number of unaccepted connections that
        # the system will allow before refusing new connections
        s.listen(5)
        print(f"[*] Listening as {SERVER_HOST}:{SERVER_PORT}")
        # accept connection if there is any
        client_socket, address = s.accept()
        # if below code is executed, that means the sender is connected
        print(f"[+] {address} is connected.")
        # receive the file infos
        # receive using client socket, not server socket
        received = client_socket.recv(BUFFER_SIZE).decode()
        filename, filesize, mod_time = received.split(SEPARATOR)
        # Convert file last modified time into float
        mod_time = float(mod_time)
        # Add server working dir
        filename = working_dir+"/"+os.path.basename(filename)
        # convert to integer
        filesize = int(filesize)
        # start receiving the file from the socket
        # and writing to the file stream
        progress = tqdm.tqdm(range(filesize), f"Receiving {filename}", unit="B", unit_scale=True, unit_divisor=1024)
        with open(filename, "wb") as f:
            while True:
                # read 1024 bytes from the socket (receive)
                bytes_read = client_socket.recv(BUFFER_SIZE)
                if not bytes_read:
                    # nothing is received
                    # file transmitting is done
                    break
                # write to the file the bytes we just received
                f.write(bytes_read)
                # update the progress bar
                progress.update(len(bytes_read))
        # update the file modified time to keep in sync with the other servers
        os.utime(filename, (mod_time, mod_time))
        # close the client socket
        client_socket.close()
        # close the server socket
        s.close()