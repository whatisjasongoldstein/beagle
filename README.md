# Beagle

Let's say you want to build a static site, but it doesn't quite
fit into Jekyll's mold, and you want a real template language
with `extends`, `includes`, and logic, as well as builtin
asset processing. 

Can Gulp do this? Yes. But the gulp package ecosystem is terrible,
debugging unpleasant, and I still have no idea what a `stream` is.

Python 3.

## Usage

A build tool for static sites. You create a simple skeleton like this:

```
myproject/
    app.py
    dist/
        # This should be empty.
        # It will be wiped/built up
        # on each build.
    src/
        index.py

```

The source folder can contain jinja2 templates, stylesheets,
images, javascript, fonts, or whatever other front end assets
you need.

`app.py` instantiates the app, and should look like this:

```
#!/usr/bin/env python

import os
import sys
import beagle

from src import index

# In theory these can live wherever you want, but you
# should keep them inside the repo.
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(PROJECT_DIR, "src")
DIST_DIR = os.path.join(PROJECT_DIR, "dist")

app = beagle.App(index, src=SRC_DIR, dist=DIST_DIR, watch="dev" in sys.argv)
```

In this example, running `./app.py` will perform all the operations in your index.
For a development server (powered by Flask), run `./app.py dev`.

Fill your index with functions that manage the build process.

```python
# Every function wrapped in an action decorator
# will run as part of the build process, and should
# return at least one Beagle command (you can put them in a list)
from beagle.decorators import action
from beagle.commands import Page, Copy, Sass, Concat

@action
def homepage():
    """
    Renders the jinja2 template `src/index.html` with the context,
    and writes the results to `dist/index.html`
    """
    return Page(template="index.html", output="index.html", context={
        "message": "Hello World"
    })

@action
def include_images():
    """
    Copy will copy a file or directory into dist.
    Since these are just python functions, you
    can do anything you want in the logic.
    """
    things = ["favicon.ico", "images"]
    copies = []
    for thing in things:
        copies.append(Copy(infile="thing"))
    return copies


@action
def css():
    """
    Takes SCSS, runs it through SASSC, 
    and outputs into the dist folder.
    """
    return Sass(file="css/app.scss", output="css/app.min.css")


@action
def js():
    """
    Rollup javascript into one file using the concat command.
    """
    return Contact(
        filenames=["jquery.js", "underscore.js", "helpers.js"],
        destination="app.min.js")

```

If `watch` is true, every time you modify a file in the source
directory, include the index, the dist will rebuild.


### Markdown

When rendering Jinja2 templates, you can use the Markdown
filter. Almost all the extensions are enabled.

```jinja2
{{ title|markdown }}

{% filter markdown %}
# Markdown is pretty great

You can use less popular features like footnotes[^1].

[^1]: Tables, smartquotes, code fencing, table of contents, and metadata should work too.
{% endfilter %}
```


### Extensibility

Subclass `beagle.commands.Command` to make new commands.

```python
class BrowserifyCmd(Command):
    """
    As an example, this runs some javascript through
    browserify.
    """

    # Set which kwargs are required
    requires = ("infile", "outfile", )

    def render(self):
        # Commands always have `self.app` set to the Beagle app
        # at the time their rendered, meaning you can reach
        # the dist and src folders.
        js_input = os.path.join(self.app.src, self.infile)
        js_output = os.path.join(self.app.dist, self.output)
        subprocess.call('browserify -e %s -o %s' % (infile, outfile), shell=True)


# And then use it like this in your index file
@action
def browserify():
    return BrowserifyCmd(infile="js/app.js", outfile="js/app.min.js")

```

Because everything here is just Python, there's no reason you can't make, for example,
database calls in your index or custom commands.

You can also pass a custom Jinja2 environment to the Beagle app constructor if you'd
like to use custom filters/etc using the kwarg `jinja_env`.

## Deployment

Point nginx at your `dist` folder.

I have some ideas about github pages but haven't tested them yet.

I bet you could even write a command that rsync'd the dist folder
to a remote server, and not even need to have your repo live on the box.

As you know, never expose your Python code to the outside world.

## I still don't get why this is a thing

I noticed that most of the tools that I struggled to make
work to build a gulp static site had command lines. They don't need
a fancy wrapper, I just needed something to run them when stuff changed.

And I just like working in Python.

### Should I use this in production?

I have no idea. I did it for fun, and to scratch my own itch.

### TODO

It'd be neat if it was smart enough to only rebuild the files you
touched, but that's really hard.
