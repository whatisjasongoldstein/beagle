def action(func):
    """
    Any function that should run as part of the 
    build process.
    """
    func._is_beagle_action = True
    return func