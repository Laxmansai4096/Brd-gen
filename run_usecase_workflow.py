import os
import sys

workspace_dir = os.path.dirname(os.path.abspath(__file__))
if workspace_dir not in sys.path:
    sys.path.insert(0, workspace_dir)

from scripts.run_usecase_workflow import run_usecase

if __name__ == "__main__":
    run_usecase()
