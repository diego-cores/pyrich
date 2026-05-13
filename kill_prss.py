"""
Kill process

Kill the 'pythonw.exe' process.
If the operating system is not Windows, the 'python' process is killed.
"""

import subprocess
import sys

if sys.platform == "win32":
    subprocess.run(["taskkill", "/f", "/im", "pythonw.exe"])
else:
    subprocess.run(["pkill", "-f", "python"])
