#!/usr/bin/python

from argparse import ArgumentParser
from os.path import abspath, exists, join
from os import getcwd, makedirs, walk
from sys import exit
from importlib import import_module
from thetvdb import thetvdb
from urllib import urlretrieve

version = '0.0'
modes = ['tv','movie']
media_extensions = ('mkv','avi','mp4','mov')
#destinations = {'tv':'/media/tv','movie':'/media/movies'}
destinations = {'tv':'/home/matt/Videos/TV'}
modules = {'tv':thetvdb.TVShow}

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

def download(url,dest_file,overwrite = False):
  """Download the url to the destination file, only overwrite if the overwrite boolean is set."""
  
  if exists(dest_file) and overwrite is False:
    return
  
  log_debug("Downloading file from %s" % url)
  log_debug("Downloading file to %s" % dest_file)
  urlretrieve(url,dest_file)

def menu(title,options):
  while True:
    print title
    print '=' * len(title)
    if type(options) is list:
      for i,option in enumerate(options):
        print "%s. %s" % (str(i),option)
    if type(options) is dict:
      for i,option in enumerate(options.itervalues()):
        print "%s. %s" % (str(i),option)
    if len(options) < 10:
      selection = int(getch())
    else:
      selection = int(raw_input())
    if selection < len(options):
      if type(options) is list:
        return options[selection]
      if type(options) is dict:
        return options.keys()[selection]
    else:
      print "Invalid selection"

argparser = ArgumentParser("Rename media files")
argparser.add_argument('--version', action='version', version=version)
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

#Load database object
#db_object = modules[mode]()
#log_debug("DB Object loaded: %s" % (str(db_object)))

#Get database ID for the working dir
if args.id:
  id = args.id[0]
  log_debug("Database ID for media set from command line as %s" % id)
else:
  search_obj = modules[mode]() if mode is 'tv' else None #TODO: movie
  log_debug("Search object created")
  print "Directory: %s" % wd
  
  term = raw_input('Search Term > ')
  log_debug("Searching database for '%s'" % str(term))
  search_results = search_obj.search(term)
  selection = menu("Database Search Results",search_results)
  id = selection
  log_debug("Database ID for media set by user as %s" % id)

#Create the database object for the specific media
if id:
  db_object = modules[mode](id) if mode is 'tv' else None #TODO: movie
  log_debug("Database object created: %s" % str(db_object))
else:
  db_object = None
  log_error("Programming error, ID is not set.")

if db_object:
  #See if the series or movie dir exists
  dest_path = join(destinations[mode],db_object.get_samba_show_name())
  if not exists(dest_path):
    log_debug("Creating directory for media: %s" % dest_path)
    makedirs(dest_path)
  else:
    log_debug("Media directory %s exists" % dest_path)
  
  #Download top-level artwork
  download(db_object.fanart_url,join(dest_path,"fanart.jpg"),overwrite=False)
  download(db_object.poster_url,join(dest_path,"folder.jpg"),overwrite=False)
  
  #Generate a list of files in working dir
  file_list = []
  for root, dirname, filenames in walk(wd):
    for filename in filenames:
      if filename.endswith(media_extensions):
        log_debug("File %s determined to be a media file. Adding it to the list" % filename)
        file_list.append(join(root,filename))
      else:
        log_debug("File %s determined to be a non-media file. Skipping this file" % filename)
  
  log_debug("File list:\n%s" % str(file_list))
  
  for filename in file_list:
    #TV specific actions
    if mode is 'tv':
      #Determine season number
      
      #Create season directory
      
      #Download artwork
      
      #Rename and move file
      
      #Download subtitles
      pass
