# Author : Remi Sarrailh
# Website : https://github.com/madnerdorg/emailcheck
# Licence  : MIT
# Check if a new email has arrived on an IMAP server
# Then execute a command (for example turn on leds)

import imaplib 
import time
import ConfigParser
import os
import sys

# TEST

previous_unread_emails = 0 
unread_emails = 0
empty_inbox = False
VER = "1.0"

emails = []
actions = []


# 
def string_between( string, first, last ):
    """ 
        **find a string between two substring**   
        Example: string_between("<hello>","<",">") -> hello  
        
        Source https://stackoverflow.com/a/3368991      
    """
    try:
        start = string.rindex( first ) + len( first )
        end = string.rindex( last, start )
        return string[start:end]
    except ValueError:
        return ""

def get_from_address(raw_header):
    """
        **get FROM email address from a raw header of an email
        **   
        Return: From Address or List-Id for mailing list
        Example: 
        raw_header = mailbox.fetch(1,'(BODY[HEADER])')   
        from_address = get_from_address(raw_header) --> user@example.com
    """
    split_header = raw_header[1][0][1].split("\n")
    from_address = ""
    # print(raw_header)
    for item in split_header:
        if item.startswith("From:"):
            from_address = string_between(item, "<", ">")    
        if item.startswith("List-Id:"):
            from_address = string_between(item, "<", ">")
    return from_address

def start_command(command):
    """
        ** Start a command and restart it if command did not return 0 **   
        Return: Exit Code --> 0 (Ok) 1 (Not OK)

        Source http://www.tldp.org/LDP/abs/html/exitcodes.html
    """
    status = os.system(command)
    print "Command returned: " + str(status)
    # If command did not complete, restart it
    if status is not 0:
        print("Command failed, retrying")
        time.sleep(settings["email"]["interval"])
        start_command(command)
    return status


def read_settings(file):
    """ Read a ini settings file and populate a dict
        return: settings_status, settings_dict
    """    
    settings_failed = False

    # Generate an empty settings with default values
    settings = {
        "general":{
            "gui":False
        },
        "email":{
            "server":"",
            "user":"",
            "password": "",
            "interval": 15
        },
        "commands":{
            "empty": "",
            "any": ""
        }
    }
    # If file exists
    if os.path.isfile(file):
        print(">>--> Open settings: " + file)
    
        # Parse ini file
        ini = ConfigParser.ConfigParser()
        ini.read(file)
        try:
            for section in ini.sections():
                if section == "general":
                    # print("...... General")
                    settings["general"]["gui"] = ini.get("general","gui")

                elif section == "email":   
                    # print("...... Email")       
                    settings["email"]["server"] = ini.get("email","server")
                    settings["email"]["user"] = ini.get("email","user")
                    settings["email"]["password"] = ini.get("email","password")
                    settings["email"]["interval"] = float(ini.get("email","interval"))

                elif section == "empty":
                    settings["commands"]["empty"] = ini.get("empty","command")
                    # print "...... Actions for empty inbox"

                elif section == "any" :
                    settings["commands"]["any"] = ini.get("any","command")
                    # print "...... Actions for any email"
                
                # If section is unknown, we assume it is an email
                else:
                    emails.append(section)
                    actions.append(ini.get(section,"command"))
                    # print "...... Actions for " + section
        except Exception as e:
            print(" " + str(e) + " ")
            raw_input("=== Press Enter to exit...") 

    else:
        print("(X_X) No " + file)
        settings_failed = True
        raw_input("=== Press Enter to exit...") 
    return settings_failed,settings


print("~~   ["+VER+"] Unread Email checker     ~~")
print("~~ github.com/madnerdorg/emailcheck ~~")
print(" ")
#################
# Settings file #
#################
settings_failed, settings = read_settings("settings.ini")

# print(settings)

####################
# Email Connection #
####################
if not settings_failed:
    print(">>--> Connect to " + settings["email"]["server"])
    try:
        mailbox = imaplib.IMAP4_SSL(settings["email"]["server"])
    except:
        print(" ")
        print(" X  Invalid email server (x_X)  X")
        raw_input(" === Press Enter to exit...") 
        settings_failed = True

if not settings_failed:
    try:
        (retcode, capabilities) = mailbox.login(settings["email"]["user"], settings["email"]["password"])
    except:
        print(" ")
        print(" X  Invalid email or password (o_O)  X")
        print(" ")
        raw_input(" === Press Enter to exit...")  
        settings_failed = True
print(" ")


####################
# Inbox Checker    #
####################

if not settings_failed:
    while True:
        mailbox.select(readonly=1) # Select inbox or default namespace
        (retcode, messages) = mailbox.search(None, '(UNSEEN)')
        messages_id = messages[0].split() # Get list of ID of unread email
        # print(messages)
        try:
            unread_emails = len(messages_id) # Get nb of unread email
        except ValueError:
            unread_emails = 0
            pass

        # If unread message nb change
        if unread_emails != previous_unread_emails and unread_emails != 0:
            print("Unread email: " + str(unread_emails))
            # Get Header from last email
            raw_header = mailbox.fetch(messages_id[-1],'(BODY[HEADER])')
            from_address = get_from_address(raw_header)
            print("~~~~~ Email "+ messages_id[-1] +" from: " + from_address)

            # Custom command
            if from_address in emails:
                id_action =  emails.index(from_address)
                start_command(actions[id_action])
            else:
            # Default command
                start_command(settings["commands"]["any"])

            #print raw_email
            empty_inbox = False
        
        # If there is no more email start empty command
        if unread_emails == 0 and not empty_inbox:
            print("Unread email: 0")
            print("~~~~~ Empty Inbox command")
            start_command(settings["commands"]["empty"])
            empty_inbox = True

        previous_unread_emails = unread_emails
        
        # Check if mailbox search for unread email is OK, else
        # display error code
        if retcode != "OK":
            print("X " + retcode + " X") 
        
        mailbox.close()

        # Wait before checking the mailbox again
        time.sleep(settings["email"]["interval"])
