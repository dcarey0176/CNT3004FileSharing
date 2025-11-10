# type_effect.py
import sys
import time
import os


if sys.stdout.isatty():
    pass
else:
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 1)  # 1 = line buffered

def type_print(text: str, delay: float = 0.03) -> None:
    """Print *text* one character at a time."""
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write('\n')
    sys.stdout.flush()

def spacing():
    print("\n" + "=" * 40)