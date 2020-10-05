# -*- coding: utf-8 -*-

from pathlib import Path
import sys

project_dir: Path = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_dir))
