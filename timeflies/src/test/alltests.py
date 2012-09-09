
import unittest
from unittest import TestCase

import re
import sys
from datetime import date

sys.path.append('..') 

from timeflies import Day, Reader, Statistics, Universe, MonthFilter

#class TestWithInputFile(TestCase):
#    def __init__(self):
#        self.uni = Universe()
#        self.reader = Reader(self.uni)
        
class DayTests(TestCase):
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

class SimpleProject(TestCase):
    def test_read(self):
        u = Universe()
        r = Reader(u)
        r.read('simple-project-1.fly')
        p1 = u.taskroot.getTask("project")
        self.assertEqual("project", p1.name)
        p2 = p1.getTask("sub2.bbb")
        self.assertEqual("bbb", p2.name)
        a = p2.activities[0]
        self.assertEqual(date(2012, 7, 14), a.day().date)

class EndToEnd(TestCase):
    def test_read(self):
        #days = r.read('H:\Timesheet\work-book.log')
        #days = r.read('work-book.log')
        u = Universe()
        r = Reader(u)
        r.read('example1.log')
        u.taskroot.dump()
        s = Statistics(u)
        s.simple()
        
class CalcActivitiesByMonth(TestCase):
    def test_read(self):
        self.u = Universe()
        r = Reader(self.u)
        r.read('simple-project-2.fly')
        p1 = self.u.taskroot.getTask("project")
        self.assertEqual("project", p1.name)
        p2 = p1.getTask("sub2.bbb")
        self.assertEqual("bbb", p2.name)
        a = p2.activities[0]
        self.assertEqual(date(2012, 7, 14), a.day().date)
        act = self.doStats(7)
        self.assertEqual(2.0, act['mother.project.sub1.aa'])
        self.assertEqual(3.0, act['mother.project.sub3'])
        self.assertEqual(10.0, act['mother.project.sub2'])
        act = self.doStats(8)
        self.assertEqual(1.5, act['mother.project.sub1.aa'])
        self.assertEqual(4.0, act['mother.project.sub1'])
        self.assertEqual(3.5, act['mother.project.sub2'])
   
    def doStats(self, month):
        print('------------------')
        act = {}
        self.u.taskroot.calcActivity(MonthFilter(2012, month), act)
        for tn in sorted(act.keys()):
            indentname = re.sub('[a-z0-9A-Z]+\.', '. . ', tn)
            print('{0:6.2f} {1:s}'.format(act[tn], indentname))
        return act
        
if __name__ == '__main__':
    unittest.main()

