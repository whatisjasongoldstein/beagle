import os
import shutil
import subprocess

from .helpers import require_directory


class Command(object):
    """
    Base command. Inherit by setting
    require and render. The app will always be available.
    """

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
    requires = ("template", "context", "outfile", )

    def render(self):
        # Ensure the output directory exists
        outfile = os.path.join(self.app.dist, self.outfile)
        require_directory(outfile)

        # Render the template in jinja2
        template = self.app.jinja.get_template(self.template)
        html = template.render(**self.context)

        # Write the file
        with open(outfile, "w") as f:
            f.write(html)


class Copy(Command):
    """
    Copy anything into dist. infile is required.
    outfile will be the same if left blank.
    """
    requires = ["infile"]
    
    def render(self):
        if not hasattr(self, "outfile"):
            self.outfile = self.infile
        infile = os.path.join(self.app.src, self.infile)
        outfile = os.path.join(self.app.dist, self.outfile)

        if os.path.isdir(infile):
            shutil.copytree(infile, outfile)
        else:
            shutil.copy(infile, outfile)


class Sass(Command):

    requires = ["infile", "outfile"]

    def render(self):
        sass_input = os.path.join(self.app.src, self.infile)
        sass_output = os.path.join(self.app.dist, self.outfile)
        require_directory(sass_output)
        subprocess.call("sassc --sourcemap %s %s" % (sass_input, sass_output), shell=True)


class Concat(Command):
    requires = ["infiles", "outfile"]

    def render(self):
        files = " ".join([os.path.join(self.app.src, f) for f in self.infiles])
        dest = os.path.join(self.app.dist, self.outfile)
        require_directory(dest)
        subprocess.call("cat %s > %s" % (files, dest), shell=True)

