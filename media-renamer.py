#!/usr/bin/python

from argparse import ArgumentParser
from os.path import abspath, exists, join, basename, splitext
from os import getcwd, makedirs, walk, rename, system
from sys import exit,stdout,stderr
from importlib import import_module
from thetvdb import thetvdb
from urllib import urlretrieve
from re import compile

version = '0.5'
modes = ['tv','movie']
media_extensions = ('mkv','avi','mp4','mov')
destinations = {'tv':'/media/tv','movie':'/media/movies'}
modules = {'tv':thetvdb.TVShow}
#Test regex here: http://www.pythonregex.com/
filename_regex = {'tv':'(?P<season>\d{1,})(?:[xXeE\,])(?P<episode>\d{1,})(?:[-\.\seE])*(?P<second_episode>\d{1,})?'}

def log_debug(message,identifier = ""):
  if args.debug:
    if identifier:
      print "Debug:\t%s:\t%s" % (identifier,message)
    else:
      print "Debug:\t%s" % (message)

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

class Progress(object):
  def __init__(self,goal,output=stdout,line_length=10):
    self.current = 0
    self.goal = goal
    self.output = output
    self.line_length = line_length
  
  def step(self):
    self.current += 1
    self.refresh()
  
  def refresh(self):
    #Clear the line and move to the beginning of the line
    self.output.write(chr(27) + '[2K\r')
    self.output.flush()
    #percent complete is calculated as a whole number (50 is 50%)
    percent_complete = int((float(self.current) / float(self.goal)) * 100)
    bars_complete = percent_complete / self.line_length
    line = '|'*bars_complete
    line = line.ljust(self.line_length,'.')
    self.output.write("%s %s%%" % (line,str(percent_complete)))
    self.output.flush()

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

def escape_path(path):
  return path.replace(' ','\ ').replace('&','\&').replace('[','\[').replace(']','\]').replace("'","\\'").replace('(','\(').replace(')','\)').replace('$','\$')

argparser = ArgumentParser("Rename media files")
argparser.add_argument('--version', action='version', version=version)
argparser.add_argument('-d','--directory',help="Directory to process",nargs=1)
argparser.add_argument('-t','--type',help="Specify the type of media being processed",nargs=1)
argparser.add_argument('-i','--id',help="ID for the show or movie on thetvdb or themoviedb",nargs=1)
argparser.add_argument('--debug',help="Display debug messages",action='store_true')
argparser.add_argument('--dry-run',help="Run the script but don't actually move or download anything",action='store_true',default=False)

args = argparser.parse_args()
print str(args)
getch = _Getch()

#all actions will be saved to this dictionary, they key will be the action
# the value will be a list of lists of parameters
# 'move':[['source1','destination1'],['source2','destination2']]
#actions: move, download
actions = {'move':[],
           'download':[],
           'mkdir':[]}

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
    if dest_path not in actions['mkdir']:
      actions['mkdir'].append(dest_path)
  else:
    log_debug("Media directory %s exists" % dest_path)
  
  #Download top-level artwork
  actions['download'].append([db_object.fanart_url,join(dest_path,"fanart.jpg")])
  actions['download'].append([db_object.poster_url,join(dest_path,"folder.jpg")])
  
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
    extension = splitext(filename)[1]
    log_debug("Extension set from filename as %s" % extension)
    #TV specific actions
    if mode is 'tv':
      #Parse filename for season/episode
      regex = compile(filename_regex[mode])
      log_debug("Running regex on file: %s" % filename)
      r = regex.search(filename)
      parts = r.groupdict() if r else None
      log_debug("File parts read as %s" % str(parts))
      
      #Determine Season
      if parts and 'season' in parts:
        season = int(parts['season'])
        log_debug("Season set from regular expression as %s" % season)
      else:
        print filename
        season = raw_input("Season Number > ")
        log_debug("Season read from user input as %s" % season)
      
      #If no season is given, assume the user cancelled
      if season is '':
        print "Skipping %s..." % filename
        continue
      
      #Create season directory
      season_path = join(dest_path,"Season %s" % (str(int(season))))
      if not exists(season_path):
        if season_path not in actions['mkdir']:
          actions['mkdir'].append(season_path)
        
        #Download artwork
        #TODO: Find a way to get the highest reviewed season art
        #download(db_object.poster_url,join(season_path,"folder.jpg"),overwrite=False)
      
      #Determine Episode
      if parts and 'episode' in parts:
        episode = int(parts['episode'])
        log_debug("Episode set from regular expression as %s" % episode)
      else:
        print filename
        episode = raw_input("Episode Number > ")
        log_debug("Episode read from user input as %s" % episode)
      
      #Rename and move file
      new_filename = db_object.get_samba_filename(season_number=season,episode_number=episode)
      new_filename += extension
      parameters = [filename,join(season_path,new_filename)]
      log_debug("Adding move entry to actions: %s -> %s" % (parameters[0],parameters[1]))
      actions['move'].append(parameters)
      
      #Download subtitles
      #TODO

if actions:
  log_debug("Processing actions:\n%s" % (str(actions)))
  print "Actions pending (%d new directories, %d moves, %d downloads)" % (len(actions['mkdir']),len(actions['move']),len(actions['download']))
  
  log_debug("Creating Progress object")
  progress = Progress(goal=len(actions['mkdir'])+len(actions['move'])+len(actions['download']))
  
  if len(actions['mkdir']):
    for directory in actions['mkdir']:
      if not exists(directory):
        if args.dry_run:
          print "Dry Run: Would create dir %s" % directory
        else:
          log_debug("Creating directory %s" % str(directory))
          makedirs(directory)
          progress.step()
  
  if len(actions['download']):
    for parameters in actions['download']:
      if len(parameters) is 2:
        if args.dry_run:
          print "Dry Run: Would download:\n\tURL: %s\n\tDestination: %s" % (parameters[0],parameters[1])
        else:
          download(parameters[0],parameters[1],overwrite=False)
          progress.step()
  
  if len(actions['move']):
    for parameters in actions['move']:
      if len(parameters) is 2:
        log_debug("Renaming file: %s -> %s" % (parameters[0],parameters[1]))
        log_debug("Escaped source: %s" % escape_path(parameters[0]))
        log_debug("Escaped destination: %s" % escape_path(parameters[1]))
        if args.dry_run:
          print "Dry Run: Would move file:\n\tSource: %s\n\tDestination: %s" % (parameters[0],parameters[1])
        else:
          #rename generates 'OSError: [Errno 18] Invalid cross-device link'
          #rename(filename,join(season_path,new_filename))
          system("mv %s %s" % (escape_path(parameters[0]),escape_path(parameters[1])))
          progress.step()
      else:
        log_error("parameters list should have exactly two elements: %s" % str(parameters))

#Print one line at the end
print ""
