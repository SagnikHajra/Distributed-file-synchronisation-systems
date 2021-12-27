#!/usr/bin/python3
'''
Name: Sagnik Hajra
ID: 1001851338
'''
import socket
import time
import os
import json
import threading
import file_exchange_client
import file_exchange_server


class SocketClass:
    def __init__(self, add, port, server=False, clientLimit=10):
        self.ADDRESS = add
        self.PORT = port
        self.HEADER_SIZE = 10
        self.MSG_SIZE = 1024
        self.FORMAT = 'utf-8'
        self.command = ''
        self.DELAY_TIME = 0.1

        self.WELCOME = "WELCOME"
        self.INVALID_COMMAND = "INVALID"
        self.CONNECTION_CLOSE = "CONNECTION_CLOSE"
        # When one server is scanning files at directories, all requests for file metadata has to wait.
        # The flag used for that is self.scanning
        self.scanning = False

        # dict(list) :- for modification time and size in bytes.
        # Will have two keys, one for deleted and another for existing files.
        self.own_file_meta_data = {}
        self.file_metadata_index = []
        self.locked_file = set()
        self.delete_queue = set()
        # dict(list) :- Keeps track of the other server file metadata
        self.others_file_meta_data = {}

        self.client_command = "lab3"
        self.exit = "exit"
        self.success = "Successful"
        self.metadata = "metadata"
        self.file_data = "file_data"
        self.FILE_SENT = "File is sent"
        self.file_metadata_key = "file_metadata"
        self.deleted_key = "deleted"
        self.accepted_commands = {self.client_command, self.file_data, self.metadata, self.exit}
        self.file_deleted = {}

        self.file_transaction_complete = True
        self.messages = {
            self.WELCOME: "Welcome to server..:",
            self.INVALID_COMMAND: "Command not found",
            self.CONNECTION_CLOSE: "Closing the connection...",
            self.success: "Request handled successfully..."
        }
        # For the 1st purpose: All server will be listening to one port(server port) to accept client requests
        if server:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.ADDRESS, self.PORT))
            self.socket.listen(clientLimit)
            print(f"{self.ADDRESS} started listening on port number {self.PORT}....")
        # For the second purpose: To send query to other servers to keep the file directory in sync
        else:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.ADDRESS, self.PORT))

    def receive(self, sock):
        """
        :param sock: socket object which is expected to receive some message from a client/server
        :return: Parse and combine all the message(s). Return when combined will have the exact length+self.HEADER_SIZE
        """
        command = ''
        new_msg = True
        msgLen = 0
        while True:
            msg = sock.recv(self.MSG_SIZE)
            if new_msg and msg:
                msgLen = int(msg[:self.HEADER_SIZE])
                new_msg = False
            command += msg.decode(self.FORMAT)
            if len(command) - self.HEADER_SIZE == msgLen:
                return command[self.HEADER_SIZE:]

    def send(self, return_msg, sock, sleep=0):
        """"
        :param return_msg: The message that needs to be sent to a client/server
        :param sock: socket object which is expected to receive some message from a client
        :param sleep: As the program is executed in local machine the network latency is almost none, sometimes forced latency is needed.
        :return: Parse/combine all the messages with header size==self.HEADER_SIZE and return
        """
        returnMsg = f"{len(return_msg):<{self.HEADER_SIZE}}" + return_msg
        time.sleep(sleep)
        sock.send(bytes(returnMsg, self.FORMAT))

    # Compare the files from others against own dir,
    # idea is to keep everything in sync and when mismatches are found, return then
    def comparing_other_server_file_dir(self):
        mismatches = []

        # For smoke, there has to be fire
        if not self.others_file_meta_data:
            return []

        own_file_metadata = self.own_file_meta_data[self.file_metadata_key]
        for key in self.others_file_meta_data:
            # If file found at other server but recently deleted from this server, ignore(Other servers aren't in sync)
            # Do the same if the file is locked
            if key in self.own_file_meta_data[self.deleted_key] or key in self.locked_file:
                continue
            # If file is missing from own metadata dictionary, add to mismatches
            if key not in own_file_metadata:
                mismatches.append(key)
                continue
            # If own file last modified time is older then add to mismatches
            if own_file_metadata[key][0] < self.others_file_meta_data[key][0]:
                mismatches.append(key)
        return mismatches

    # Each server invokes this thread as soon as they start
    # Keep scanning for files in their own directory(then refresh the metadata database) as well as other server(s)
    # takes a 5 sec nap in between
    def get_synced(self):
        while True:
            # print("syncing started..")
            self.scan_file_metadata()
            self.fetch_from_other_server(meta_data=True)
            mismatches = self.comparing_other_server_file_dir()
            if mismatches:
                print(mismatches)
                file_names = "||".join(mismatches)
                self.fetch_from_other_server(data_file=file_names)
            # print("syncing finished..")
            time.sleep(5)

    # Below method deletes a file when the same file is deleted from other server(s) to be in sync
    def delete_files(self, deleted):
        for files in deleted:
            if files in self.own_file_meta_data[self.file_metadata_key]:
                if files not in self.locked_file:
                    self.delete_a_file(files)
                else:
                    self.delete_queue.add(files)
                    print(self.delete_queue)

    # delete a single file
    def delete_a_file(self, file):
        del self.own_file_meta_data[self.file_metadata_key][file]
        self.file_metadata_index.remove(file)
        file_name = f"{self.workingDir}/{file}"
        if os.path.isfile(file_name):
            os.remove(file_name)

    # Interpret messages coming from clients
    def interpret_message(self, message, metadata=False):
        if metadata:
            details_of_files = json.loads(message)
            # print(details_of_files)
            if details_of_files[self.deleted_key]:
                self.delete_files(details_of_files[self.deleted_key])
            self.others_file_meta_data = details_of_files[self.file_metadata_key]

    # The below function will act like a client to the origin server and fetch fle info
    def fetch_from_other_server(self, meta_data=False, data_file=""):
        # Handle error when any destination is unreachable. People don't like to read red error messages. Be coool!
        try:
            socket = SocketClass('localhost', self.parallel_server_port)
        except ConnectionRefusedError:
            print(f"Connection was refused by localhost:{self.parallel_server_port}. Please check the connection.")
            return

        # Close the socket
        def close_socket():
            # print(f"Message received, closing the sync of {obj.PRT} socket")
            socket.socket.close()

        while True:
            server_msg = socket.receive(socket.socket)
            if server_msg == socket.CONNECTION_CLOSE:
                return close_socket()
            elif server_msg == socket.WELCOME:
                if meta_data:
                    socket.send(self.metadata, socket.socket)
                elif data_file:
                    socket.send(f"{self.file_data}:{data_file}", socket.socket)
                    data_file = ""
            elif server_msg not in socket.messages:
                self.interpret_message(server_msg, metadata=meta_data)
            # elif server_msg in socket.messages[server_msg]:
            #     print(socket.messages[server_msg])

    # Check for existing, new and deleted files. Stores at global var own_file_meta_data. Which has two keys.
    # One for deleted files and another for existing and new files. self doesn't care about which files are new
    # That's other servers' business
    def scan_file_metadata(self):
        self.scanning = True
        tmp_file_meta_data = {}
        tmp_file_metadata_index = []
        deleted = []

        for item in os.listdir(self.workingDir):
            file_path = self.workingDir + "/" + item
            if os.path.isfile(file_path):
                tmp_file_meta_data[str(item)] = [os.path.getmtime(file_path), os.path.getsize(file_path)]
                tmp_file_metadata_index.append(str(item))
        # When there are files in directory, else add blank to all the file metadata variables
        if self.own_file_meta_data:
            old_file_meta_data = self.own_file_meta_data[self.file_metadata_key]

            for key in old_file_meta_data:
                if key not in tmp_file_meta_data:
                    deleted.append(key)
                    self.file_metadata_index.remove(key)
        self.own_file_meta_data[self.deleted_key] = deleted
        self.own_file_meta_data[self.file_metadata_key] = tmp_file_meta_data
        self.file_metadata_index = tmp_file_metadata_index

        # print(self.own_file_meta_data)
        self.scanning = False

    # One job of each server is to send the files that are requested by other server(s). The below function is for that
    def send_files(self, file_names):
        mismatches = []
        print(f"The following files were received: {file_names}")
        for files in file_names.split("||"):
            mismatches.append(files)
        result = file_exchange_client.send_all_files(self.workingDir, mismatches, self.file_excng_client_port)
        if not result:
            print("Got all files")
        else:
            print(f"The following files are not synced: {result}")

    def create_json_dump(self):
        if not self.locked_file:
            return json.dumps(self.own_file_meta_data)
        else:
            output = {}
            output[self.deleted_key] = self.own_file_meta_data[self.deleted_key]
            output[self.file_metadata_key] = {}

            for file in self.own_file_meta_data[self.file_metadata_key]:
                if file not in self.locked_file:
                    output[self.file_metadata_key][file] = self.own_file_meta_data[self.file_metadata_key][file]
            return json.dumps(output)

    # the below function interprets the commands received from client
    def parse_message(self, client_socket=socket):
        close_the_socket = True
        if self.command in self.accepted_commands:
            if self.command == self.metadata:
                # Server needs to wait while another thread is scanning the metadata
                while self.scanning:
                    time.sleep(.01)
                # If the server is scanning flag False, return the file metadata
                return self.create_json_dump(), close_the_socket
            elif self.command == self.client_command:
                close_the_socket = False
                while self.scanning:
                    time.sleep(.01)
                return self.nicer(), close_the_socket
            else:
                close_the_socket = False
                return self.INVALID_COMMAND, close_the_socket
        elif self.command.split("-")[0].strip() == self.client_command:
            close_the_socket = False
            option, file_idx = self.command.split("-")[1], self.command.split("-")[2]
            option, file_idx = option.strip(), file_idx.strip()
            try:
                file_idx = int(file_idx)
                if file_idx >= len(self.file_metadata_index):
                    raise ValueError
                file_name = self.file_metadata_index[file_idx]
                if option == "unlock" and file_name not in self.locked_file:
                    raise ValueError
            except ValueError:
                close_the_socket = False
                return self.INVALID_COMMAND, close_the_socket

            while self.scanning:
                time.sleep(.01)
            if option == "lock":
                self.locked_file.add(file_name)
                return self.success, close_the_socket
            elif option == "unlock":
                self.locked_file.remove(file_name)
                if file_name in self.delete_queue:
                    self.delete_a_file(file_name)
                    self.delete_queue.remove(file_name)
                return self.success, close_the_socket
            else:
                close_the_socket = False
                return self.INVALID_COMMAND, close_the_socket

        elif self.command.split(":")[0] == self.file_data:
            file_names = self.command.split(':')[1]
            print(f"{time.ctime(time.time())}| request for file {file_names} has been received")
            self.send_files(file_names)
            return "Finished sending", close_the_socket
        else:
            close_the_socket = False
            return self.INVALID_COMMAND, close_the_socket

    def handle_client(self, client_socket):
        # Send the welcome message
        self.send(self.WELCOME, client_socket)
        while True:
            self.command = self.receive(client_socket)
            if self.command:
                if self.command.strip() == self.exit:
                    close_the_socket = True
                else:
                    return_msg, close_the_socket = self.parse_message()
                    self.send(return_msg, client_socket, self.DELAY_TIME)
                # For claen exit
                if close_the_socket:
                    self.send(self.CONNECTION_CLOSE, client_socket, self.DELAY_TIME)
                    client_socket.close()
                    return

    def start(self):
        """ :job: Starts three different types of threads,
                last one connects with the client, recv command from client, parse the command and respond back
            :returns: None
        """
        # Thread Type1: Accept files from other server
        file_exchange_thread = threading.Thread(
            target=file_exchange_server.receiver, args=(self.workingDir, self.file_excng_server_port,)
        )
        file_exchange_thread.start()

        # Thread Type2: Continue the syncing process every 5 secs
        server_thread = threading.Thread(target=self.get_synced)
        server_thread.start()

        # Thread Type2: Get the client details after accepting a request and send the welcome message
        while True:
            client_socket, (clientAdd, clientPort) = self.socket.accept()
            # print(f"{time.ctime(time.time())}| connection from {clientAdd, clientPort} has been established")
            thread = threading.Thread(target=self.handle_client, args=(client_socket,))
            thread.start()
            active_count = threading.active_count() - 1
            # print(f"Number of Threads active:{active_count}")

    def nicer(self):
        """ :return: human readable metadata of all the files in the system master directory """
        res = ""
        # Fetch the file metadata from global obj variable file_metadata_key
        file_list = self.own_file_meta_data[self.file_metadata_key]
        index = 0
        try:
            for file in self.file_metadata_index:
                # Get the metadata of each file
                file_name = file
                last_modified_time = file_list[file][0]
                size = file_list[file][1]
                # Convert the metadata into human readable format
                readable_time = self.get_file_datetime(last_modified_time)
                readable_size = self.human_readable_bytes(size)
                # Add if any file is locked
                locked_status = "|| [Locked]" if file in self.locked_file else ""
                # Append with final result
                res += f'[{index}]||{readable_time}||{readable_size}||{file_name}{locked_status}\n'
                index += 1
            if not res:
                res = "|| || ||\n"
        except KeyError:
            print(self.own_file_meta_data)
            return "|| || ||\n"
        return res

    # returns human readable datetime
    def get_file_datetime(self, time_second):
        """
        :param time_second: Last modification time of a file in second with decimal value
        :return: datetime in format like :     Mon Aug 30 14:48:46 2021
        """
        return time.ctime(time_second)

    # Below code was copied from stackoverflow. Link is given
    # https://stackoverflow.com/questions/12523586/python-format-size-application-converting-b-to-kb-mb-gb-tb/63839503
    def human_readable_bytes(self, size):
        """
        :param self: object of either ServerA or ServerB
        :param size: The size of a file in byte
        :return: most feasible human friendly KB, MB, GB, or TB string
        """
        B = float(size)
        KB = float(1024)
        MB = float(KB ** 2)  # 1,048,576
        GB = float(KB ** 3)  # 1,073,741,824
        TB = float(KB ** 4)  # 1,099,511,627,776

        if B < KB:
            return_str = '{0} {1}'.format(B, 'Bytes' if 0 == B > 1 else 'Byte')
        elif KB <= B < MB:
            return_str = '{0:.2f} KB'.format(B / KB)
        elif MB <= B < GB:
            return_str = '{0:.2f} MB'.format(B / MB)
        elif GB <= B < TB:
            return_str = '{0:.2f} GB'.format(B / GB)
        elif TB <= B:
            return_str = '{0:.2f} TB'.format(B / TB)

        # Return a string of length 15. If len(return_str) < 15 then add spaces at the end
        return return_str + " " * (15 - len(return_str))
