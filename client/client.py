import socket
import sys
from os.path import *
from os import makedirs
from os import listdir


class InvalidCommandException(Exception):
    """
    Generic bad command exception.
    Handled in main loop of handle_client()
    """
    pass


# set of valid command headers
valid_headers = ['GET', 'PUT', 'LS']

# various usage messages, compiled into one place and easy to acquire based on command header
usage_messages = {
    'GET': 'Usage: GET remote-path local-path',
    'PUT': 'Usage: PUT local-path remote-path',
    'LS': 'Usage: LS client|server'
}

# get connection info from command line args
host = sys.argv[1]
port = int(sys.argv[2])

try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # our connection to the server
    print(f'Connecting to {host} on port {port}...')
    s.connect((host, port))
    print(f'Successfully connected to {host} on port {port}')
except socket.error:
    print('Error creating socket.')
    sys.exit(1)


def print_invalid_filepath():
    """
    Error message if filepath is invalid
    :return: none
    """
    print('Please select a valid file path.')


def print_connection_error():
    """
    Generic error message
    :return: none
    """
    print('There was a problem communicating with the server.')


def valid_command(command: str):
    """
    Sends command to server and waits for server to confirm that command is valid on its end.
    Always called after local arg is validated, when necessary.
    :param command: the command being validated
    :return: True if server confirms command is valid, false otherwise
    """

    validator = {  # inverted version of the server's validator
        'VALID': True,
        'INVALID': False
    }

    s.send(command.encode('utf-8'))
    received = s.recv(1024).decode('utf-8')  # blocking
    is_valid = validator[received]
    print(f'Server says command \'{command}\' is {received}, {"forwarding" if is_valid else "aborting"}...')
    return is_valid


def pprint_dir(target: str, files: str):
    """
    Pretty print for the directory requested with LS.
    :param target: 'client' or 'server'
    :param files: newline-delimited string, representing list of files to be printed
    :return: none
    """
    print(f'\nCurrent files in {target}\'s directory:')
    print('-' * 20)
    print(files)
    print('-' * 20 + '\n')


def main():
    """
    Main driver program for client.

    Main loop:
    1. Takes command
    2. Validates command locally
    3. Sends command to server, validates on their end
    4. Waits for server info (if necessary)
    5. Executes locally

    :return: none
    """

    global s

    def get():
        """
        Asks server for the contents of file at source-path and saves them into file at destination-path
        :return: none
        """
        if len(args) != 3:
            raise InvalidCommandException
        path = args[2]  # with GET, the path that the client cares about is the destination
        try:
            path = abspath(path)
            if not exists(dirname(path)):  # make path if it does not already exist
                makedirs(dirname(path), True)
                print(f'Created directories \'{dirname(path)}\'')
        except OSError:  # recover from garbage paths
            print_invalid_filepath()
            raise InvalidCommandException
        if not valid_command(command):  # abort if server does not validate
            raise InvalidCommandException
        with open(path, 'w') as f:
            print(f'Successfully created file \'{basename(path)}\' at directory \'{dirname(path)}\'')
            data = s.recv(4096).decode('utf-8')
            if data != '\00':  # receiving only a NULL character means that the file was blank
                f.write(data)
                print(f'Successfully wrote to \'{path}\'')
            else:
                print(f'File requested was blank, file \'{basename(path)}\' created but nothing written.')

    def put():
        """
        Gets contents from file at source-path and gives them to server to put at destination-path.
        :return: none
        """
        if len(args) != 3:
            raise InvalidCommandException
        path = args[1]  # with PUT, the path that the client cares about is the source
        try:
            path = abspath(path)
            if not exists(path):  # can't pull from a file that does not exist
                print(f'File at {path} does not appear to exist.')
                raise InvalidCommandException
        except OSError:  # recover from garbage paths
            print_invalid_filepath()
            raise InvalidCommandException
        if not valid_command(command):  # abort if server does not validate
            raise InvalidCommandException
        with open(path, 'r') as f:
            data = f.read(4096)
            s.send(data.encode('utf-8'))

    def ls():
        """
        Prints list of files in current working directory for either client or server.
        :return: none
        """
        if len(args) != 2:
            raise InvalidCommandException
        target = args[1]  # either 'client' or 'server'
        if target == 'client':  # no need to interact with the server at all
            files = '\n'.join(listdir(curdir))
        elif target == 'server':
            if not valid_command(command):  # abort if server does not validate
                raise InvalidCommandException
            encoded = s.recv(4096)
            files = encoded.decode('utf-8')
        else:
            raise InvalidCommandException
        pprint_dir(target, files)

    while True:
        command = input('Enter an SFMP command: ')

        if command == 'quit':
            s.close()
            sys.exit(0)

        args = command.split(' ')
        header = args[0].upper()

        try:
            if header in valid_headers:
                locals()[header.lower()]()  # execute function specified by header
            else:
                raise InvalidCommandException
        except ConnectionError:
            print_connection_error()
            break
        except InvalidCommandException:
            print('Please select a valid command.\n')
            if header in valid_headers:
                print(f'{usage_messages[header]}\n')
            else:
                print(*usage_messages.values(), sep='\n')
            continue


main()
