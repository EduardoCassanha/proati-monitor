import subprocess
import sys
import os

dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard.py")

subprocess.Popen(
    ["cmd", "/k", f"python {dashboard_path}"],
    creationflags=subprocess.CREATE_NEW_CONSOLE,
)