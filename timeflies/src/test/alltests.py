
import unittest

import sys
from datetime import date

sys.path.append('..') 

from timeflies import Day, Reader, Statistics, Universe

class DayTests(unittest.TestCase):
    def test_createDay(self):
        d = Day('2012-08-05')
        self.assertEqual(d.date, date(2012, 8, 5))

    def test_simpleBalance(self):
        d = Day('2012-08-05')
        self.assertEqual(d.calcBalance(), 0)
        d.setHours(8, 17)
        self.assertEqual(d.calcBalance(), 9)
        d.addOff(1)
        self.assertEqual(d.calcBalance(), 8)

class EndToEnd(unittest.TestCase):
    def test_read(self):
        u = Universe()
        r = Reader(u)
        #days = r.read('H:\Timesheet\work-book.log')
        #days = r.read('work-book.log')
        r.read('example1.log')
        u.taskroot.dump()
        s = Statistics(u);
        s.simple();
        
if __name__ == '__main__':
    unittest.main()

