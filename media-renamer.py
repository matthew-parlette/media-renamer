#!/usr/bin/python

from argparse import ArgumentParser
from os.path import abspath
from os import getcwd

modes = ['tv','movie']
destinations = {'tv':'/media/tv','movie':'/media/movies'}

def log_debug(message,identifier = ""):
  if args.debug:
    if identifier:
      print "Debug:\t%s:\t%s" % (identifier,message)
    else:
      print "Debug:\t\t%s" % (message)

def log_error(message,identifier = ""):
  if args.debug:
    if identifier:
      print "Error:\t%s:\t%s" % (identifier,message)
    else:
      print "Error:\t\t%s" % (message)

## {{{ http://code.activestate.com/recipes/134892/ (r2)
class _Getch:
    """Gets a single character from standard input.  Does not echo to the screen."""
    def __init__(self):
        try:
            self.impl = _GetchWindows()
        except ImportError:
            self.impl = _GetchUnix()

    def __call__(self): return self.impl()


class _GetchUnix:
    def __init__(self):
        import tty, sys

    def __call__(self):
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch


class _GetchWindows:
    def __init__(self):
        import msvcrt

    def __call__(self):
        import msvcrt
        return msvcrt.getch()

## end of http://code.activestate.com/recipes/134892/ }}}

def menu(title,options):
  while True:
    print title
    print '=' * len(title)
    for i,option in enumerate(options):
      print "%s. %s" % (str(i),option)
    selection = int(getch())
    if selection < len(options):
      return options[selection]
    else:
      print "Invalid selection"

argparser = ArgumentParser("Rename media files")
argparser.add_argument('-d','--directory',help="Directory to process",nargs=1)
argparser.add_argument('-t','--type',help="Specify the type of media being processed",nargs=1)
argparser.add_argument('-i','--id',help="ID for the show or movie on thetvdb or themoviedb",nargs=1)
argparser.add_argument('--debug',help="Display debug messages",action='store_true')

args = argparser.parse_args()

getch = _Getch()

#Get working directory
if args.directory:
  wd = abspath(args.directory[0])
  log_debug("Working directory read from command line as %s" % wd)
else:
  wd = abspath(getcwd())
  log_debug("Working directory defaulted to current directory of %s" % wd)

#Determine mode
if args.type and args.type in modes:
  mode = args.type[0]
  log_debug("Media type set from command line as %s" % mode)
else:
  mode = menu("Media Type",options=modes)
  log_debug("Media type set from user selection as %s" % mode)

