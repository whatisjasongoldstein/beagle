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

try:
    from pync import Notifier
except ImportError:
    Notifier = None


class Page(object):
    """
    A templating object.
    """
    def __init__(self, output, template, context):
        self.output = output
        self.template = template
        self.context = context


def action(func):
    """
    Any function that should run as part of the 
    build process.
    """
    func._is_beagle_action = True
    return func

# Setup Flask app, which will be our dev server
from flask import Flask
app = Flask(__name__, static_folder="dist")

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/<path:path>')
def everything_else(path):
    # send_static_file will guess the correct MIME type
    return app.send_static_file(path)


class Engine(object):

    def __init__(self, index, src=None, dist=None):
        self.index = index
        self.src = src
        self.dist = dist

        # Set flask to serve from the right directory
        app.static_folder = self.dist

    def render(self):
        importlib.reload(self.index)
    
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

        env = Environment(loader=FileSystemLoader(self.src))
        for page in project_index["pages"]:
            template = env.get_template(page["template"])
            html = template.render(**page.get("context", {}))
            with open(os.path.join(self.dist, page["output"]), "w") as f:
                f.write(html)

        for sass in project_index.get("sass", []):
            sass_input = os.path.join(self.src, sass["file"])
            sass_output = os.path.join(self.dist, sass["output"])
            subprocess.call("sassc --sourcemap %s %s" % (sass_input, sass_output), shell=True)
        
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

        class AssetMaker(FileSystemEventHandler):
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
        event_handler = AssetMaker()
        observer = Observer()

        observer.schedule(event_handler, self.src, recursive=True)
        observer.start()
        try:
            # Run Simple python server
            # run_server()
            app.run()
        except KeyboardInterrupt:
            observer.stop()
        observer.join()

