#!/usr/local/bin/python2.7
# encoding: utf-8
'''
mailbell -- checks an email account for new messages with a certain subject and plays a sound

mailbell is a simple script that checks for new messages on an IMAP mail server and 
executes some action for every mail found. It can easily be extended with 
new notification actions

It defines classes_and_methods

@author:     Stefan Zollinger
        
@copyright:  2013 Stefan Zollinger
        
@license:    Apache

@contact:    stefan.zollinger@gmail.com
@deffield    updated: Updated
'''

import sys
import os

from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
import imaplib
import subprocess


class Notification(object):
    
    def __init__(self, **kwargs):
        self.opts = kwargs
        self.setup()
        
    def setup(self):
        raise NotImplementedError( "Should have implemented this" )
    
    def notify(self):
        raise NotImplementedError( "Should have implemented this" )
        
class ShellNotification(Notification):

    def setup(self):
        import subprocess

    def notify(self):
        if "debug" in self.opts:
            print "Executing %s" % self.opts["cmd"]
        subprocess.call(self.opts["cmd"], shell=True)
        

class PygameSoundNotification(Notification):
    ''' Not finished '''
    
    def setup(self):
        if not "audio_file" in self.opts:
            raise Exception("Needs audio file to play.")
        
        pygame.init()
        pygame.mixer.init(44100, -16, 2, 2048)
        self.sound = pygame.mixer.Sound(self.opts["audio_file"])
        
    def notify(self):
        print "Playing sound"
        self.sound.play()


class MailBell(object):
    
    last_checked_file = os.path.join("data", "last_checked")
    last_checked_date = None
    opts = {}
    debug = False
    
    def __init__(self, notification, **kwargs):
        self.notification = notification
        self.opts = kwargs

        self.debug = self.opts.get("debug", False)
        
    
    def notify(self):
        self.notification.notify()

    def check(self):
        
        user = self.opts.get("user", False)
        pwd = self.opts.get("password", False)
        
        # connecting to the gmail imap server
        m = imaplib.IMAP4_SSL(self.opts.get("server"))
        m.login(user, pwd)
        
        readonly = self.debug
        
        m.select(self.opts.get("folder", "INBOX"), readonly=readonly) # Choose the folder to read from
        
        search = "UNSEEN"

        if "match_body" in self.opts:
            search += " BODY \"%s\"" % self.opts["match_body"]
        if "match_subject" in self.opts:
            search += " subject \"%s\"" % self.opts["match_subject"]
            
        
        resp, data = m.search(None, "(%s)" % search) # Could filter using the IMAP rules here (check http://www.example-code.com/csharp/imap-search-critera.asp)
        
        for num in data[0].split():
            if not readonly:
                m.store(num, "+FLAGS", "\\Seen")
            self.notify()
            
            

def main(argv=None): # IGNORE:C0111
    '''Command line options.'''
    
    if argv is None:
        argv = sys.argv
    else:
        sys.argv.extend(argv)

    program_name = os.path.basename(sys.argv[0])
    program_shortdesc = __import__('__main__').__doc__.split("\n")[1]
    program_license = '''%s

  Copyright 2013 Stefan Zollinger. All rights reserved.
  
  Licensed under the Apache License 2.0
  http://www.apache.org/licenses/LICENSE-2.0
  
  Distributed on an "AS IS" basis without warranties
  or conditions of any kind, either express or implied.

USAGE
''' % (program_shortdesc)

    try:
        # Setup argument parser
        parser = ArgumentParser(description=program_license, formatter_class=RawDescriptionHelpFormatter)
        parser.add_argument("cmd", help="Command to execute for each message found")
        parser.add_argument("-d", "--debug", dest="debug", help="Turn on debug output. Messages don't get status 'read'")
        parser.add_argument("-u", "--user", dest="user", default="", help="IMAP user" )
        parser.add_argument("-p", "--password", dest="password", default="", help="IMAP password")
        parser.add_argument("-s", "--server", dest="server", default="localhost", help="IMAP mail server")
        parser.add_argument("-f", "--folder", dest="folder", help="IMAP folder to check")
        parser.add_argument("--body", dest="match_body", help="Search in mail body for this term")
        parser.add_argument("--subject", dest="match_subject", help="Search term for mail subject")
        # Process arguments
        args = parser.parse_args()
        
        notifier = ShellNotification(cmd=args.cmd, debug=args.debug)
        m = MailBell(notifier, **vars(args))
        m.check()

        return 0
    except KeyboardInterrupt:
        # Handle keyboard interrupt 
        return 0


if __name__ == "__main__":
    sys.exit(main())
