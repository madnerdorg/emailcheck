# Author : Remi Sarrailh
# Website : https://github.com/madnerdorg/emailcheck
# Licence MIT
# Check if a new email has arrived on an IMAP server
# Then execute a command (for example turn on leds)
# Check madnerd.org for more information.

import imaplib 
import time
"""
imap_server = "ssl0.imapserver.net"
imap_user = "user@address.org"
imap_password = "BatteryHorseStaple"
command = 'ws-send.exe --url "wss://localhost:42001" --message "/on"'
commandOff = 'ws-send.exe --url "wss://localhost:42001" --message "/off"'
"""
interval = 15
previous_email_num = 0
noemail = False

import os
while True:
    
    conn = imaplib.IMAP4_SSL(imap_server)

    try:
        (retcode, capabilities) = conn.login(imap_user, imap_password)
    except:
        print sys.exc_info()[1]
        sys.exit(1)

    conn.select(readonly=1) # Select inbox or default namespace
    (retcode, messages) = conn.search(None, '(UNSEEN)')
    try:
        email_num = len(messages[0].split())
    except ValueError:
        email_num = 0
        pass
    
    if email_num > previous_email_num:
        print("Notify me")
        os.system(command)
        noemail = False
    if email_num == 0 and not noemail:
        os.system(commandOff)
        noemail = True

    previous_email_num = email_num
    print(email_num)
    conn.close()
    time.sleep(interval)
