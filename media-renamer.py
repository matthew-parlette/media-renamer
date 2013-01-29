#!/usr/bin/python

from argparse import ArgumentParser

argparser = ArgumentParser("Rename media files")
argparser.add_argument('-d','--directory',help="Directory to process",nargs=1)
argparser.add_argument('-t','--type',help="Specify the type of media being processed",nargs=1)
argparser.add_argument('-i','--id',help="ID for the show or movie on thetvdb or themoviedb",nargs=1)
argparser.add_argument('--debug',help="Display debug messages",action='store_true')

args = argparser.parse_args()
