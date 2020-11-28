'''
@date: 22/11/2020
@author: Ernesto Lowy
@email: ernestolowy@gmail.com
'''
from configparser import ConfigParser
import os
import pdb

DEFAULT_CONFIG_FILE = 'settings.ini'
def get_config_file():
    return os.environ.get('CONFIG_FILE', DEFAULT_CONFIG_FILE)

CONFIG_FILE = get_config_file()

def create_config(config_file=None):
    parser = ConfigParser()
    parser.read(config_file or CONFIG_FILE)
    return parser

CONFIG = create_config()