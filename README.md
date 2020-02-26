# SFTP
SFTP is a fake file transfer protocol similar in nature to FTP, with a client-server architecture. There are three SFTP commands:
1. `GET`: get a file from the server
2. `PUT`: put a file on the server
3. `LS`: list all files in a directory on the client or server

GET and PUT support filenames, relative paths and absolute paths, if they exist. You can also change the filetype of a file created using GET or PUT, for instance from a `txt` to a `csv`. Note that this is undefined behavior and is likely to break things if you're not careful.

# Example client syntax:
- `GET mytext.txt new_mytext.txt` - Takes `mytext.txt` from the server's directory, if it exists, and sends it to the client, saving it to the client's working directory as `new_mytext.txt`
- `PUT local.txt remote.txt` - Takes `local.txt` from the client's directory, if it exists, and sends it to the server, saving it to the server's working directory as `remote.txt`
- `LS client` - Prints all files in the client's working directory
- `LS server` - Prints all files in the server's working directory

There are no user inputs for the server, however the server will print all activity with a timestamp.
