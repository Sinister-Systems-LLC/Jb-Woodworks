#!/usr/bin/env python3
import re, sys
p = sys.argv[1]
data = open(p, 'rb').read()
# Find header: '\xf0\x9f\x93\xa6\n<NUM> /_dlopen_tmp_entry.js\n\xe2\x9c\x84\n'
m = re.match(rb"^(\xf0\x9f\x93\xa6\n)(\d+)( /_dlopen_tmp_entry\.js\n\xe2\x9c\x84\n)", data)
if not m:
    print("no header match"); sys.exit(1)
header_pre = m.group(1)
declared = int(m.group(2))
header_post = m.group(3)
body = data[m.end():]
actual = len(body)
print(f"declared={declared} actual={actual}")
if declared != actual:
    new_data = header_pre + str(actual).encode() + header_post + body
    open(p, 'wb').write(new_data)
    print(f"updated header to {actual}")
