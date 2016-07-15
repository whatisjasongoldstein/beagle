import shutil
import json
import subprocess
import os
import sys
import time
import logging
import importlib
from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler, FileSystemEventHandler
from jinja2 import Environment, FileSystemLoader
from pync import Notifier


class Page(object):
    def __init__(self, output, template, context):
        self.output = output
        self.template = template
        self.context = context


def mug(func):
    func._is_mug = True
    return func