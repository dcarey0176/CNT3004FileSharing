# type_effect.py
import sys
import time
import os

# --------------------------------------------------------------
# 1. Force LINE-BUFFERED output (works in every IDE)
# --------------------------------------------------------------
if sys.stdout.isatty():
    # Running in a real terminal → keep normal buffering
    pass
else:
    # Running in an IDE → force line buffering
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 1)  # 1 = line buffered

# --------------------------------------------------------------
# 2. The actual typewriter function
# --------------------------------------------------------------
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