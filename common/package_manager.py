import time
import pip

def install(package):
    pip.main(['install', package])

def install_requirements(file):
    pip.main(['install', '-r', file, "--upgrade"])

def check_dulwich():
    needwait = False
    for i in range(2):
        if needwait:
            time.sleep(3)
            needwait = False
        try:
            import dulwich
            return
        except ImportError:
            try:
                install('dulwich')
            except:
                needwait = True
    try:
        import dulwich
    except ImportError:
        raise ImportError("Unable to import dulwich")