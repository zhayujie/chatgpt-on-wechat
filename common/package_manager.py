import pip

def install(package):
    pip.main(['install', package])

def install_requirements(file):
    pip.main(['install', '-r', file, "--upgrade"])

def check_dulwich():
    try:
        import dulwich
        return
    except ImportError:
        install('dulwich')
    raise ImportError("Unable to import dulwich")