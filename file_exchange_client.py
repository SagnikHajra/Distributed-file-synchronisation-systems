#!/usr/bin/python3
'''
Name: Sagnik Hajra
ID: 1001851338

Code copied and modified
Ref: https://www.thepythoncode.com/article/send-receive-files-using-sockets-python
'''
import socket
import time
import tqdm
import os


# Will receive the filename and PORT number from invoker(SocketClass)
def sender(filename, port):
    SEPARATOR = "<SEPARATOR>"
    BUFFER_SIZE = 4096 # send 4096 bytes each time step
    # the ip address or hostname of the server, the receiver
    host = "127.0.0.1"
    # get the file size
    filesize = os.path.getsize(filename)
    # Get the last modification time
    mod_time = os.path.getmtime(filename)
    # create the client socket
    s = socket.socket()

    # Connecting to the server:
    print(f"[+] Connecting to {host}:{port}")
    try:
        s.connect((host, port))
    except ConnectionRefusedError as err:
        print(f"Connection was refused by localhost:{port}. Please check the connection.")
        return False
    print("[+] Connected.")

    # send the filename and filesize
    s.send(f"{filename}{SEPARATOR}{filesize}{SEPARATOR}{str(mod_time)}".encode())

    # start sending the file
    progress = tqdm.tqdm(range(filesize), f"Sending {filename}", unit="B", unit_scale=True, unit_divisor=1024)
    with open(filename, "rb") as f:
        while True:
            # read the bytes from the file
            bytes_read = f.read(BUFFER_SIZE)
            if not bytes_read:
                # file transmitting is done
                break
            # we use sendall to assure transimission in
            # busy networks
            s.sendall(bytes_read)
            # update the progress bar
            progress.update(len(bytes_read))
    # close the socket
    s.close()
    return True


def send_all_files(parent_dir, file_list, port):
    result = []
    parent_dir = parent_dir+"/"
    for file in file_list:
        val = sender(parent_dir+file, port)
        if not val:
            result.append(file)
        time.sleep(0.2)
    return result
