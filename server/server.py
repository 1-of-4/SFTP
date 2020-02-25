import socket
import threading
from datetime import datetime
from os.path import *
from os import makedirs
from os import listdir

# dict of clients, out of scope of everything so its always visible
# shouldn't cause threading issues, by nature of how connections work
clients = {}

# set of valid request headers to check against
valid_headers = ['GET', 'PUT', 'LS']


class InvalidCommandException(Exception):
    """
    Exception to be raised when the validator is 'INVALID'.
    Handled in main loop of handle_client()
    """
    pass


class EmptyFileException(Exception):
    """
    Exception to be raised when file requested using GET is blank.
    Handled in main loop of handle_client()
    """
    pass


def dprint(s: str):
    """
    Prints with timestamp. All prints on the server use this.
    :param s: string to append to timestamp
    :return: none
    """
    print(f'[{datetime.now().strftime("%H:%M:%S.%f")}]\t{s}')


def num_clients():
    """
    Prints the number of clients connected.
    :return: none
    """
    dprint(f'Clients connected: {len(clients)}')


def handle_client(conn: socket.socket, address: (str, int)):
    """
    Main logic that handles an individual client's thread.
    Checks for a valid header, confirms that relevant args (usually paths) are valid, and executes.
    :param conn: connection to particular client
    :param address: address of client
    :return: none
    """

    def esend(s: str):
        """
        Utility function, stands for 'encode and send'
        Since we're always encoding in utf-8 before sending, we might as well roll it into one function
        :param s: the data to encode and send, pre-formatted to a string for simplicity's sake
        :return: none
        """
        conn.send(s.encode('utf-8'))

    def vprint(is_valid: bool):
        """
        Utility function, stands for 'validate and print'.
        Sends a VALID or INVALID message to the client, and prints an appropriate message to stdout.
        :param is_valid: boolean signifying whether request is valid
        :return: none
        """

        # mini-dict to cut down on conditionals
        validator = {
            True: 'VALID',
            False: 'INVALID'
        }

        esend(validator[is_valid])
        dprint(f'Request from {address} is {validator[is_valid]}, replying{" and discarding" if not is_valid else ""}...')

    def get():
        """
        Retrieves a file from the requested filepath and sends its contents to the client.
        :return: none
        """
        if len(args) != 3:
            raise InvalidCommandException
        path = args[1]  # the path to pull the file from
        try:
            if exists(path):  # validate existence of requested file
                vprint(True)
            else:
                raise OSError
        except OSError:  # catch-call for if file does not exist or is inaccessible
            raise InvalidCommandException
        with open(path, 'r') as f:
            data = f.read(4096)
            if not data:  # if file is blank
                dprint(f'File at \'{path}\' is blank, informing client...')
                esend('\00')  # send() doesn't like to send empty strings, so send unicode NULL character instead to "finish" conversation
                raise EmptyFileException  # reset
            else:
                esend(data)
        dprint(f'File at \'{abspath(path)}\' successfully sent to client at {address}')

    def put():
        """
        Takes data received from client and puts it into a specified file.
        :return: none
        """
        if len(args) != 3:
            raise InvalidCommandException
        path = args[2]  # where to put the file sent by the client
        try:
            path = abspath(path)
            dirs = dirname(path)
            if not exists(dirs):  # make path if it doesn't already exist
                makedirs(dirs, True)
                dprint(f'Directory \'{dirs}\' created')
            vprint(True)
        except OSError:  # check for validity of path (sanity check to avoid gibberish paths)
            raise InvalidCommandException
        with open(path, 'w+') as f:
            data = conn.recv(4096).decode('utf-8')
            if data:
                f.write(data)
        dprint(f'File \'{basename(path)}\' successfully created in directory \'{dirs}\'')

    def ls():
        """
        Lists the files in the server's working directory.
        :return: none
        """
        target = args[1]
        if target == 'server' and len(args) == 2:
            vprint(True)
            ls_list = listdir(curdir)  # generates list of all elements in working directory (since LS doesn't take a path)
            num_elements = len(ls_list)
            data = '\n'.join(ls_list)  # converts to newline-delimited string for easy sending and processing
            esend(data)
            dprint(f'Sent list containing {num_elements} entries to client at {address}')
        else:  # should never fire with a well-written client, but you never know
            raise InvalidCommandException

    # main loop of the client
    while True:
        try:
            command = conn.recv(1024).decode('utf-8')  # should be sufficient bytes for a pair of sane file paths
            args = command.split(' ')  # break command into args for easier processing
            dprint(f'Received request \'{command}\' from client at {address}')

            header = args[0].upper()  # on the off chance that the client doesn't check for lowercase headers
            if header in valid_headers:  # GET, PUT, or LS
                locals()[header.lower()]()  # run the corresponding function
            else:  # more insurance against poorly-designed clients
                raise InvalidCommandException

        except ConnectionError:  # catch-all for connection problems, breaks loop and ultimately kills current thread
            dprint(f'Client at {address} has disconnected')
            break
        except InvalidCommandException:  # raised during validation, resets conversation
            vprint(False)
            continue
        except EmptyFileException:  # raised when file requested using GET is blank
            continue

    conn.close()  # close socket
    del clients[address]  # remove client from dict
    num_clients()  # display the updated number of clients


def main():
    """
    Main server engine.
    Starts socket and spins up new threads to manage new connections.
    Probably thread-safe.
    :return: none
    """
    host = '0.0.0.0'  # assigned
    port = 0xDEAD  # 57005, my preferred dynamic port

    s = socket.socket()
    s.bind((host, port))
    s.listen(10)  # 10 simultaneous clients is reasonable for an FTP server
    dprint(f'Server is listening for connections on port {port}...')

    while True:
        client, address = s.accept()  # blocking
        dprint(f'Received connection from new client at {address}')
        clients[address] = threading.Thread(target=handle_client, args=(client, address))  # assign connection to its own thread for processing
        num_clients()  # now's a good time to display the number of clients
        clients[address].start()  # start client thread
        clients[address].join()


main()
