import subprocess
import os
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
requirements_file = os.path.join(script_dir, "requirements.txt")

if not os.path.exists(requirements_file): # check for existing file
    print("no requirements.txt found :( please make sure your dependencies file is in the same directory as this file and is named \"requirements.txt\")")
    sys.exit(1)

try:
    print("Installing modules...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", requirements_file])
    print("All modules sucessfully installed")
except subprocess.CalledProcessError:
    print("Process failed")