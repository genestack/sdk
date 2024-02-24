import os
version = os.environ.get('SDK_VERSION')
if version is not None:
    __version__ = version
else:
    __version__ = "1.0.0"
