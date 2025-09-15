import socket
import getpass

username = getpass.getuser()
hostname = socket.gethostname()
print(username + "@" + hostname[:hostname.index(".local")] + ":~$ ")