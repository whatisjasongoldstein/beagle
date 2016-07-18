import os
from beagle.decorators import action
from beagle.commands import Page, Copy, Concat, Sass


@action
def main():
    """
    Single page
    """
    return Page(template="index.html", outfile="index.html", context={})

@action
def pages_based_on_directory():
    """
    Scan a directory for markdown files, and make a page for each one
    """
    md_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "markdown")
    files = os.listdir(md_folder)
    pages = []

    for filename in files:
        if filename.endswith(".md"):
            name, ext = filename.split(".")
            page = Page(template="md-page.html", outfile="%s.html" % name,
                context={
                    "doc": "markdown/%s" % filename,
                })
            pages.append(page)
    return pages


@action
def css():
    """
    Compile a sass file
    """
    return Sass(infile="site.scss", outfile="site.css")


@action
def copy_javascript():
    """
    No preporessing for this js.
    """
    return Copy(infile="site.js")
