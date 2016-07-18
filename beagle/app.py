import shutil
import json
import os
import sys
import time
import logging
import importlib
import jinja2
from werkzeug.exceptions import NotFound
import markdown
from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler, FileSystemEventHandler


Notifier = None
try:
    from pync import Notifier
except ImportError:
    pass


class App(object):

    def __init__(self, index, src=None, dist=None, watch=False, jinja_env=None):
        self.index = index
        self.src = src
        self.dist = dist


        # Allow passing a custom jinja2 env
        if jinja_env:
            self.jinja = jinja_env
        else:
            self.setup_jinja2()

        self.render()
        if watch:
            self.watch()

    def setup_jinja2(self):
        self.jinja = jinja2.Environment(loader=jinja2.FileSystemLoader(self.src))
        self.jinja.trim_blocks = True
        self.jinja.lstrip_blocks = True

        md = markdown.Markdown(output_format="html5",
            extensions=[
                'markdown.extensions.meta',
                'markdown.extensions.fenced_code',
                'markdown.extensions.footnotes',
                'markdown.extensions.toc',
                'markdown.extensions.tables',
                'markdown.extensions.codehilite',
                'markdown.extensions.sane_lists',
                'markdown.extensions.smarty',
                'markdown.extensions.smart_strong',
                ])
        self.jinja.filters['markdown'] = lambda text: jinja2.Markup(md.convert(text))

    def do_action(self, action):
        assets = action()

        # Assets are always a list
        if not hasattr(assets, "__iter__"):
            assets = (assets, )

        for asset in assets:
            asset.set_app(self)
            asset.render()


    def render(self):
    
        # Cleanup dist and ensure folders exist if --clean
        if "--clean" in sys.argv:
            shutil.rmtree(self.dist)

        if not os.path.exists(self.dist):
            os.mkdir(self.dist)

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

            # urls that end with a / are prolem index-wrapping
            if path.endswith("/"):
                path = "%sindex.html" % path

            try:
                # send_static_file will guess the correct MIME type
                return server.send_static_file(path)
            except NotFound:
                # If the file doesn't exist, assume it should
                # be an html file.
                return server.send_static_file("%s.html" % path)

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

