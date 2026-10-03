#!/usr/bin/env python3
import os
import sys
from pathlib import Path


def main():
    from config import env

    env.load_dotenv(Path(__file__).resolve().parents[2] / ".env")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
