# Geneva Smith
# Simple Mail Client
# ----------------------------------------------------------------
# This program allows users to send e-mails via the command line.
# It takes the recipient's e-mail and mail server as command line
# arguements and requests the message and sender's e-mail during
# execution. Optionally, users ca specify the -s parameter to send
# messages to gmail servers. This will require an additional
# password.
# THIS SCRIPT USES PYTHON 2.7
# ----------------------------------------------------------------

# Import libraries
import sys
import socket
import ssl
import base64
import getpass

sslEnable = False

# Check command line arguements
if (len(sys.argv) > 4):
    sys.exit("Too many arguements. Mail client closing.")
elif (len(sys.argv) < 3):
    sys.exit("Too few arguements. Mail client closing.")

# Create client socket
clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Check for SSL switch -s and assign mail server and port
if (sys.argv[1] == '-s')&(len(sys.argv) == 4):
    sslEnable = True
    mailserver = sys.argv[3]
    mailport = 587
    recipient = sys.argv[2]
else:
    mailserver = sys.argv[2]
    mailport = 25
    recipient = sys.argv[1]

# Establish TCP connection
clientsocket.connect((mailserver, mailport))

connect = clientsocket.recv(1024)
if (connect[:3] != '220'):
    sys.exit("220 Reply not received from server (CONNECT)")
print connect

# Initialize TLS
if (sslEnable):
    # Send HELO command to allow sending of TLS request
    helo = 'EHLO ' + mailserver + '\r\n'
    clientsocket.send(helo)

    helorecv = clientsocket.recv(1024)
    if (helorecv[:3] != '250'):
        sys.exit("250 Reply not received from server (HELO TLS)")
    print helorecv
    
    clientsocket.send('STARTTLS\r\n')

    tlsrecv = clientsocket.recv(1024)
    if (tlsrecv[:3] != '220'):
        sys.exit("250 Reply not received from server (TLS)")
    print tlsrecv

    # Create SSL socket
    clientsocket = ssl.wrap_socket(clientsocket, ssl_version=ssl.PROTOCOL_SSLv23)

# Send HELO command to allow sending of mail
helo = 'HELO ' + mailserver + '\r\n'
clientsocket.send(helo)

helorecv = clientsocket.recv(1024)
if (helorecv[:3] != '250'):
    sys.exit("250 Reply not received from server (HELO)")
print helorecv    

if (sslEnable):
    # Authentication required for Google mail servers
    clientsocket.send('AUTH LOGIN\r\n')
    print clientsocket.recv(1024)

    print "Enter your Google e-mail: "
    username = raw_input("~")
    print "Enter your password: "
    password = getpass.getpass("~")

    username = base64.b64encode(username)
    password = base64.b64encode(password)
    sender = username

    clientsocket.send(username + '\r\n')
    print clientsocket.recv(1024)
    clientsocket.send(password + '\r\n')
    print clientsocket.recv(1024)

else:
    print "Enter your e-mail: "
    sender = raw_input("~")

# Send MAIL FROM command
mailfrom = 'MAIL FROM: <' + sender + '>\r\n'
clientsocket.send(mailfrom)

mailfromrecv = clientsocket.recv(1024)
if (mailfromrecv[:3] != '250'):
    sys.exit("250 Reply not received from server (MAIL FROM)")
print mailfromrecv

# Send RCPT TO command
rcptto = 'RCPT TO: <' + recipient + '>\r\n'
clientsocket.send(rcptto)

rcpttorecv = clientsocket.recv(1024)
if (rcpttorecv[:3] != '250'):
    sys.exit("250 Reply not received from server (RCPT TO)")
print rcpttorecv

# Send DATA command
datacmd = 'DATA\r\n'
clientsocket.send(datacmd)

datacmdrecv = clientsocket.recv(1024)
if (datacmdrecv[:3] != '354'):
    sys.exit("354 Reply not received from server (DATA)")
print datacmdrecv

# Send message
msg = raw_input("~")

while(msg != '.'):
    clientsocket.send(msg + "\n")
    msg = raw_input("~")

clientsocket.send("\r\n.\r\n")

msgrecv = clientsocket.recv(1024)
if (msgrecv[:3] != '250'):
    sys.exit("250 Reply not received from server (MESSAGE)")
print msgrecv

# Send QUIT command
quitcmd = 'QUIT\r\n'
clientsocket.send(quitcmd)

quitcmdrecv = clientsocket.recv(1024)
if (quitcmdrecv[:3] != '221'):
    sys.exit("221 Reply not received from server (QUIT)")
print quitcmdrecv

# Close socket
clientsocket.close()
