"""
Root Entrypoint for Email Automation System
Allows running the Streamlit dashboard, CLI, or tasks from the repository root directory.
"""

import os
import sys

# Ensure root workspace is in sys.path
root_dir = os.path.dirname(os.path.abspath(__file__))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from main import main

if __name__ == '__main__':
    main()
