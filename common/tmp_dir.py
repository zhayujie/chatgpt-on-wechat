import os
import pathlib

from config import conf


class TmpDir(object):
    """A temporary directory that is deleted when the object is destroyed."""

    tmpFilePath = pathlib.Path("./tmp/")

    def __init__(self):
        os.makedirs(self.tmpFilePath, exist_ok=True)

    def path(self):
        return str(self.tmpFilePath)
