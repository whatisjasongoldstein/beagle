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

is_dev = "dev" in sys.argv

Notifier = None
if is_dev:
    try:
        from pync import Notifier
    except ImportError:
        pass


class Command(object):

    app = None
    requires = []

    def __init__(self, **kwargs):
        
        # Ensure that all required kwargs are present
        for key in self.requires:
            if key not in kwargs:
                raise Exception("Required kwarg missing: %s" % key)

        # Set all kwargs on the class
        for k, v in kwargs.items():
            setattr(self, k, v)

    def set_app(self, app):
        self.app = app

    def render(self):
        raise Exception("You need to implement a render method.")


class Page(Command):
    """
    A templating object.
    """
    requires = ("template", "context", "output", )

    def render(self):
        template = self.app.jinja.get_template(self.template)
        html = template.render(**self.context)
        with open(os.path.join(self.app.dist, self.output), "w") as f:
            f.write(html)


class CopyDir(Command):
    requires = ["directory", "output"]
    
    def render(self):
        shutil.copy(self.directory, self.output)


class Sass(Command):

    def render(self):
        sass_input = os.path.join(self.app.src, self.file)
        sass_output = os.path.join(self.app.dist, self.output)
        subprocess.call("sassc --sourcemap %s %s" % (sass_input, sass_output), shell=True)


def action(func):
    """
    Any function that should run as part of the 
    build process.
    """
    func._is_beagle_action = True
    return func

server = None
if is_dev:

    # Setup Flask app, which will be our dev server
    from flask import Flask
    server = Flask(__name__, static_folder="dist")

    @server.route('/')
    def index():
        return server.send_static_file('index.html')


    @server.route('/<path:path>')
    def everything_else(path):
        # send_static_file will guess the correct MIME type
        return server.send_static_file(path)


class Engine(object):

    def __init__(self, index, src=None, dist=None):
        self.index = index
        self.src = src
        self.dist = dist

        # Set flask to serve from the right directory
        if server:
            server.static_folder = self.dist

        self.jinja = Environment(loader=FileSystemLoader(self.src))

        self.render()
        if is_dev:
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

        with open(os.path.join(self.src, "index.json"), "r") as f:
            project_index = json.load(f)

        importlib.reload(self.index)

        keys = dir(self.index)
        for key in keys:
            if key.startswith("__"):
                continue
            attr = getattr(self.index, key, None)
            if hasattr(attr, "_is_beagle_action"):
                self.do_action(attr)

        # js_input = os.path.join(PROJECT_DIR, "static/js/app.js")
        # js_output = os.path.join(PROJECT_DIR, "static/js/app.min.js")
        # subprocess.call("browserify %s -t [ babelify --presets [ es2015 ] ] --output %s" % (js_input, js_output), shell=True)
        self.notify("Built your code! 🐶")

    def notify(self, message):
        if Notifier:
            Notifier.notify(message, title="Beagle")        
        else:
            print(message)

    def watch(self):
        
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

