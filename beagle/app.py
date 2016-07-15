import shutil
import json
import os
import sys
import time
import logging
import importlib
from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler, FileSystemEventHandler
from jinja2 import Environment, FileSystemLoader


Notifier = None
try:
    from pync import Notifier
except ImportError:
    pass


class App(object):

    def __init__(self, index, src=None, dist=None, watch=False):
        self.index = index
        self.src = src
        self.dist = dist

        # Set flask to serve from the right directory
        # if server:
        #     server.static_folder = self.dist

        self.jinja = Environment(loader=FileSystemLoader(self.src))

        self.render()
        if watch:
            self.watch()

    def do_action(self, action):
        assets = action()

        # Assets are always a list
        if not hasattr(assets, "__iter__"):
            assets = (assets, )

        for asset in assets:
            asset.set_app(self)
            asset.render()


    def render(self):
    
        # Cleanup dist and ensure folders exist
        shutil.rmtree(self.dist)
        required_folders = (
            self.dist,
            os.path.join(self.dist, "css"),
            os.path.join(self.dist, "js"),
        )
        for folder in required_folders:
            try:
                os.mkdir(folder)
            except FileExistsError:
                pass

        importlib.reload(self.index)

        keys = dir(self.index)
        for key in keys:
            if key.startswith("__"):
                continue
            attr = getattr(self.index, key, None)
            if hasattr(attr, "_is_beagle_action"):
                self.do_action(attr)

        self.notify("Built your code! 🐶")

    def notify(self, message):
        if Notifier:
            Notifier.notify(message, title="Beagle")        
        else:
            print(message)

    def watch(self):
        
        server = None

        # Setup Flask app, which will be our dev server
        from flask import Flask
        server = Flask(__name__, static_folder="dist")
        server.static_folder = self.dist

        @server.route('/')
        def index():
            return server.send_static_file('index.html')


        @server.route('/<path:path>')
        def everything_else(path):
            # send_static_file will guess the correct MIME type
            return server.send_static_file(path)

        render = self.render

        class RenderOnChangeHandler(FileSystemEventHandler):
            """
            Restart and when anything in src changes.
            """
            def on_modified(self, *args, **kwargs):
                render()
                # python = sys.executable
                # os.execl(python, python, *sys.argv)
        
        # Setup observer
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S')
        event_handler = RenderOnChangeHandler()
        observer = Observer()

        observer.schedule(event_handler, self.src, recursive=True)
        observer.start()
        try:
            # Run Simple python server
            # run_server()
            server.run()
        except KeyboardInterrupt:
            observer.stop()
        observer.join()

