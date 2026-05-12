"""
Kill process

Kill the 'pythonw.exe' process
"""

import subprocess
import sys

if sys.platform == "win32":
    subprocess.run(["taskkill", "/f", "/im", "pythonw.exe"])
else:
    subprocess.run(["pkill", "-f", "pythonw"])
