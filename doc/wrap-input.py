#!/usr/bin/python3

import sys

print('% autogenerated from: ' + sys.argv[1])
print('\\begin{inputfile}')
f = open(sys.argv[1])
for line in f:
    print(line, end='')
f.close()
print('\\end{inputfile}')

exit(0)
