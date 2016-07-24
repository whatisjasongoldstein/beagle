import gc
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
    """
    index
      - Python module that contains @action functions, which are executed
        to build the site
    src
      - Absolute path to the site's source directory
    dist
      - Absolute path to the site's build directory
    watch
      - Boolean. Should we start a Flask server and autobuild for development?
    jinja_env
      - Custom jinja2 environment for... special cases I haven't thought of?
    url_prefix
      - Used when the site will live under a path, such as mysite.com/foo/ instead
        of simply mysite.com. This is meant to help work on github pages, and
        will make the development server behave as expected.
    """
    def __init__(self, index, src=None, dist=None, watch=False, jinja_env=None, url_prefix="/"):
        self.index = index
        self.src = src
        self.dist = dist

        # Set url prefix for developing github pages
        self.url_prefix = url_prefix

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
        self.jinja.auto_reload = True

        md = markdown.Markdown(output_format="html5",
            extensions=[
                'markdown.extensions.meta',
                'markdown.extensions.fenced_code',
                'markdown.extensions.footnotes',
                'markdown.extensions.toc',
                'markdown.extensions.tables',
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

    def clean(self):
        """
        Since dist can be a separate repo or symlink, we
        can't just drop the whole folder, only its contents.
        """
        for filename in os.listdir(self.dist):

            # Don't delete hidden files
            if filename.startswith("."):
                continue

            filepath = os.path.join(self.dist, filename)
            if os.path.isdir(filepath):
                shutil.rmtree(filepath)
            else:
                os.remove(filepath)

    def render(self):

        if not os.path.exists(self.dist):
            os.mkdir(self.dist)
    
        # Cleanup dist and ensure folders exist if --clean
        if "--clean" in sys.argv:
            self.clean()

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

        @server.route(self.url_prefix)
        def index():
            return server.send_static_file('index.html')

        @server.route('%s<path:path>' % self.url_prefix)
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
                # Loading templates and classes over and over
                # causes gradual memory usage to creep up.
                # The garbage collector should fire every
                # after automatic renders to prevent this.
                gc.collect()
        
        # Setup observer
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S')

        observer = Observer()
        observer.schedule(RenderOnChangeHandler(), self.src, recursive=True)
        observer.start()

        try:
            # Run Simple python server
            server.run()
        except KeyboardInterrupt:
            observer.stop()
        observer.join()

