import sys
from keypad_studio.runner import extract_latest

if __name__ == "__main__":
    extract_latest(sys.argv[1], sys.argv[2])
