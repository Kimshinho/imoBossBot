
import re

def parse_time(text):

    pattern = r'^([01]?\d|2[0-3]):?([0-5]\d)$'

    match = re.match(pattern, text)

    if not match:
        return None

    return match.groups()
