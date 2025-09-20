import socket
import getpass
import os

def ls (arg = 'arg'):
    if arg != 'arg':
        if os.path.exists(arg):
            print('ls', arg)
        else:
            print(f"ls: cannot access '{arg}': No such file or directory")
    else:
        print('ls')

def cd(arg = 'arg'):
    if arg != 'arg':
        if os.path.isdir(arg):
            print('cd', arg)
        else:
            print(f"cd: {arg}: No such directory")
    else:
        print('cd')

username = getpass.getuser()
hostname = socket.gethostname()
f = True

while f:
    print(username + "@" + hostname[:hostname.index(".local")] + ":~$ ", end="")
    str = input()
    splitStr = list(str.split(" "))
    while len(splitStr) != 0 and f:
        if splitStr[0] == 'ls':
            if len(splitStr) == 1 or splitStr[1] == 'ls' or splitStr[1] == 'cd':
                ls()
                splitStr = splitStr[1:]
            else:
                ls(splitStr[1])
                splitStr = splitStr[2:]
        elif splitStr[0] == 'cd':
            if len(splitStr) == 1 or splitStr[1] == 'ls' or splitStr[1] == 'cd':
                cd()
                splitStr = splitStr[1:]
            else:
                cd(splitStr[1])
                splitStr = splitStr[2:]
        elif splitStr[0] == "exit":
            if len(splitStr) == 1:
                f = False
            else:
                try:
                    code = int(splitStr[1])
                    exit(code)
                except ValueError:
                    print("exit: numeric argument required")
                    splitStr = splitStr[2:]
        else:
            print("command ", splitStr[0], " not found")
            splitStr = splitStr[1:]
