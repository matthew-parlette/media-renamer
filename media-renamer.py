#!/usr/bin/python

from argparse import ArgumentParser

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

argparser = ArgumentParser("Rename media files")
argparser.add_argument('-d','--directory',help="Directory to process",nargs=1)
argparser.add_argument('-t','--type',help="Specify the type of media being processed",nargs=1)
argparser.add_argument('-i','--id',help="ID for the show or movie on thetvdb or themoviedb",nargs=1)
argparser.add_argument('--debug',help="Display debug messages",action='store_true')

args = argparser.parse_args()

