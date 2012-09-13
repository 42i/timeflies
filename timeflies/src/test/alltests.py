
'''

    TimeFlies is a work log and task tree processor.
    
    Copyright (C) 2012 Joerg Bullmann (jb@heilancoo.net)

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
    
'''

import unittest
from unittest import TestCase

#import re
import sys
from datetime import date

sys.path.append('..') 

from timeflies import Day, Reader, Statistics, Universe, MonthFilter, main

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
        p1 = u.taskroot.getNode("project")
        self.assertEqual("project", p1.name)
        p2 = p1.getNode("sub2.bbb")
        self.assertEqual("bbb", p2.name)
        a = p2.activities[0]
        self.assertEqual(date(2012, 7, 14), a.day().date)

class EndToEnd(TestCase):
    def test_read(self):
        main('run -b example1.log'.split(' '))
        
class CalcActivitiesByMonth(TestCase):
    def test_read(self):
        self.u = Universe()
        r = Reader(self.u)
        r.read('simple-project-2.fly')
        p1 = self.u.taskroot.getNode("project")
        self.assertEqual("project", p1.name)
        p2 = p1.getNode("sub2.bbb")
        self.assertEqual("bbb", p2.name)
        a = p2.activities[0]
        self.assertEqual(date(2012, 7, 14), a.day().date)
        act = self.doStats(7)
        self.assertEqual(2.0, act.getNode('project.sub1.aa').value)
        self.assertEqual(3.0, act.getNode('project.sub3').value)
        self.assertEqual(10.0, act.getNode('project.sub2').value)
        act = self.doStats(8)
        self.assertEqual(1.5, act.getNode('project.sub1.aa').value)
        self.assertEqual(4.0, act.getNode('project.sub1').value)
        self.assertEqual(3.5, act.getNode('project.sub2').value)
   
    def doStats(self, month):
        print('------------------')
        act = self.u.taskroot.calcActivity(MonthFilter(2012, month))
        act.dump()
        return act
        
if __name__ == '__main__':
    unittest.main()
