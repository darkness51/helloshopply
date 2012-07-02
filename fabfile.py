import os
import boto
from fabric.api import env, sudo, cd, local
from fabric.operations import get, put, open_shell
from fabric.colors import green, red
from pprint import pprint

