
import sys
from datetime import date

sys.path.append('..') 

from timeflies import Day, Reader, Statistics, Universe

d = Day('2012-08-05')
print(d.date)
assert(d.date == date(2012, 8, 5))
assert(0 == d.calcBalance())
d.setHours(8, 17)
assert(9 == d.calcBalance())
d.addOff(1)
assert(8 == d.calcBalance())
u = Universe()
r = Reader(u)
#days = r.read('H:\Timesheet\work-book.log')
#days = r.read('work-book.log')
r.read('example1.log')
u.taskroot.dump()
s = Statistics(u);
s.simple();
