# Beagle

Let's say you want to build a static site, but it doesn't quite
fit into Jekyll's mold, and you want a real template language
with `extends`, `includes`, and logic, as well as builtin
asset processing. 

Built in Python 3.

### Should I use this in production?

No! This is an experimental toy project. I don't maintain it.

## Usage

`pip install git+git@github.com:whatisjasongoldstein/beagle.git@master#egg=beagle`

Create a simple skeleton like this:

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
you need, as well as Python files that dictate what to do with
all this stuff.

`app.py` instantiates the app, and should look like this:

```python
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
    Leaving the `outfile` option off will put it in
    the same place.
    """
    return [
        Copy(infile="favicon.ico"),
        Copy(infiles="images/")
    ]


@action
def css():
    """
    Takes SCSS, runs it through SASSC, 
    and outputs into the dist folder.
    """
    return Sass(infile="css/app.scss", outfile="css/app.min.css")


@action
def js():
    """
    Rollup javascript into one file using the concat command.
    """
    return Concat(
        infiles=["jquery.js", "underscore.js", "helpers.js"],
        outfile="app.min.js")

```

If `watch` is true, every time you modify a file in the source
directory, include the index, the dist will rebuild.

You'll notice these functions are just Python -- there's nothing
stopping you from querying a sqlite database, pulling from an API,
iterating over all the files in `os.path.dirname(os.path.abspath(__file__))`
to do something special with all the markdown files in a given directory,
or any other wizardry you can dream up in Python.

None of this should require special knowledge outside of how to do 
stuff in Python.

### Markdown

When rendering Jinja2 templates, you can use the Markdown
filter. Almost all the extensions are enabled.

```html+jinja
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


## Custom Jinja2 Environment

If you don't like the default jinja2 environment, you can override it by
subclassing the app. Here's an example that adds a date format filter.

```python
#!/usr/bin/env python

import os
import sys
import beagle

from src import index

def datetimeformat(value, format='%H:%M / %d-%m-%Y'):
    return value.strftime(format)


class BetterApp(beagle.App):

    def setup_jinja2(self):
        env = super(BetterApp, self).setup_jinja2()
        env.filters['datetimeformat'] = datetimeformat
        return env


PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(PROJECT_DIR, "src")
DIST_DIR = os.path.join(PROJECT_DIR, "dist")

app = BetterApp(index, src=SRC_DIR, dist=DIST_DIR, watch="dev" in sys.argv)
```

## Deployment

Point nginx at your `dist` folder.

I have some ideas about github pages but haven't tested them yet.

I bet you could even write a command that rsync'd the dist folder
to a remote server, and not even need to have your repo live on the box.

As you know, never expose your Python code to the outside world.

### Github pages

To deploy to Github pages, set up dist to write to the repo's gh-pages
branch, and add the dist folder to your `.gitignore` file.

Github pages are weird, because they serve out of yourname.github.io/reponame/,
meaning the base url is on a path.

To tell the development server to behave the same way, you can pass `url_prefix`
as a kwarg to the Beagle app.

```python
app = beagle.App(index, src=SRC_DIR, dist=DIST_DIR, watch=True, url_prefix="/reponame/")
```

You'll need to code all the links/assets in your source directory to start with `/reponame/`,
and the Flask development server will serve `dist` to that url.

### I still don't get why this is a thing

I noticed that most of the tools that I struggled to make
work to build a gulp static site had command lines. They don't need
a fancy wrapper, I just needed something to run them when stuff changed.

And I just like working in Python.

### TODO

- [ ] It'd be neat if it was smart enough to only rebuild the files you
touched, but that's really hard.
- [ ] The Jinja2 environment is recreated between builds because constantly adding
  new templates causes its memory overhead to grow infinitely over time.
