import os

def require_directory(path):
    """
    Create the directory in this path
    if it doesn't exist already
    """
    outdir = os.path.dirname(path)
    if not os.path.exists(outdir):
        try:
            os.makedirs(outdir)
        except FileExistsError:
            pass