import datetime
import os


def read_file(filename):
    addon_dir = os.path.join(os.path.dirname(__file__))
    template_file = filename
    file_full_path = os.path.join(addon_dir, template_file)
    with open(file_full_path, "r", encoding="utf-8") as f:
        return f.read()


def now():
    current_date = datetime.datetime.now()
    return current_date.strftime("%Y-%m-%d___%H-%M-%S")
