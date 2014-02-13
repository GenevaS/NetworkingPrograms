The was implemented using Python 2.7 

To send mail to non-TLS/SSL mail servers on port25 you must execute the script using:

python mymail.py <recipient address> <smpt server>

To send mail to servers that use TLS/SSL for security purposes on port587, such as Google (gmail.com), you must execute the script with the -s option:

python mymail.py -s <recipient address> smpt.gmail.com

You will be prompted to provide the sender's e-mail address before you can send mail to the servers. For non-TLS/SSL servers, this is not required to ensure 
that mail is sent but is required to ensure that the mail is received. Not including a valid sending e-mail address might cause the mail server to automatically 
filter your message out as spam and will not be forwarded. For servers protected by TLS/SSL, entering a valid address and password is required and your message 
will not be accepted by the server if the address and password pair cannot be validated. E-mails and passwords entered during this step are sent over the TCP 
connection as base 64 encrypted values. Your password will be masked by the script.

You can begin to enter your e-mail message when you are prompted with a tilda (~) symbol. You can continue to enter text, including carriage returns, until you 
enter a period (.) on a newline. The script will append the appropriate (\r\n.\r\n) message terminator to your message.

If any of the server responses indicate a failure, the mail client will terminate and indicate which step caused the failure.