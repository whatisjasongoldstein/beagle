import os
import shutil
import subprocess


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
    requires = ("template", "context", "output", )

    def render(self):
        template = self.app.jinja.get_template(self.template)
        html = template.render(**self.context)
        with open(os.path.join(self.app.dist, self.output), "w") as f:
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

    def render(self):
        sass_input = os.path.join(self.app.src, self.file)
        sass_output = os.path.join(self.app.dist, self.output)
        subprocess.call("sassc --sourcemap %s %s" % (sass_input, sass_output), shell=True)