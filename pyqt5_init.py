#
# Added by conan-pyqt for adding Qt libraries in PATH before importing

import os as _os
_os.environ['PATH'] = _os.path.join(_os.path.dirname(__file__), "Qt", "bin") + ";" + _os.environ['PATH']