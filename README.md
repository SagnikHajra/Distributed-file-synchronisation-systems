# Overview
Each Server uses two different ports
* One for exchanging files with parallel servers
* Another for all other communications like client handling, exchanging messages with other parallel servers etc.

When a file is locked by a client, there won't be any change made to the file even if it is modified/deleted at another server
However, one has to execute ServerA.py and ServerB.py for servers and client.py for client.
## Used Language
>> Python 3.10
## Installation
```bash
pip install tqdm
```
## Server Flow
* Each server creates three different threads on startup 
  * Thread for client handling
  * Thread for file sync-up with the parallel server(s) in every 5 seconds
  * Thread exchanging files with parallel servers
*  Client handling thread with listen to any client communication and when received will parse the message and send necessary reply
*  Thread for file sync-up with the parallel server(s) will keep listening to any incoming file. When a serverA requests a file from serverB, the serverB sends that file to serverA and serverA's file-sync-up server will receive the file and make changes to it's own directory

## Client Flow
Each server supports 9 client connections at a time.
Though the code is designed to enable client communicate with any of the server, by default it is directed to serverB
* Client will send command
  * To get the file metadata of current instance of all servers
  * To lock a file by index number(sent by server)
  * To unlock a locked file by index number(sent by server)
  
# Settings

| Server   |  Address  | Listening/Connects to | Working dir | file_exc_server listening on | 
| -------- | --------- | --------------------- | ----------- | ---------------------------- |
| ServerA  | localhost |        8001           |   servera   |             5001             | 
| ServerB  | ''(Blank) |        9001           |   serverb   |             6001             |
| Client   |    N/A    |     8001/9001         |     N/A     |             N/A              |
 
## Code exec steps:
1: Unzip all files.
1: Change the self.workingDir of each ServerA.py and ServerB.py. They should be two different locations.
1: python3 ServerB.py
1: python3 ServerA.py
1: python3 client.py [whenever needed].
1: Add/remove/edit files
## Accepted Clients Commands:
```bash
lab3
lab3 -lock -<file index>
lab3 -unlock -<file index>
```
 
