import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))
from db_models.cities import Cities
from db_models.users import Users
from db_models.tasks import Tasks
