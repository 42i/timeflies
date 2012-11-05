
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

import os
import sys
from datetime import date

sys.path.append('..') 

from timeflies import Day, Reader, Universe, MonthFilter, main, set_output_destination

import subprocess

def do_main(cmdline):
    main(cmdline.split(' '))
    
class OutputWrapper:
    def __init__(self, filename):
        self._filename = filename
        self._check_filename = filename + '.check'
        self._check_file = open(self._check_filename, mode='w')
        set_output_destination(self._check_file)
    
    def compare(self):
        self._check_file.close()
        lines = 0
        diffcmdline = 'diff ' + self._filename + ' ' + self._check_filename
        for i in subprocess.getoutput(diffcmdline).splitlines():
            if lines == 0:
                print(diffcmdline)
            print(i)
            lines += 1
        
        os.remove(self._check_filename)
        return lines == 0
        
#class TestWithInputFile(TestCase):
#    def __init__(self):
#        self.uni = Universe()
#        self.reader = Reader(self.uni)
        
class DayTests(TestCase):
    def test_createDay(self):
        d = Day('2012-08-05')
        self.assertEqual(d.date, date(2012, 8, 5))

    def test_simpleHave(self):
        d = Day('2012-08-05')
        self.assertEqual(d.calc_have(), 0)
        d.set_hours(8, 17)
        self.assertEqual(d.calc_have(), 9)
        d.add_off(1)
        self.assertEqual(d.calc_have(), 8)

class SimpleProject(TestCase):
    def test_read(self):
        u = Universe()
        r = Reader(u)
        r.read('simple-project-1.fly')
        p1 = u.get_workpackage("project")
        self.assertEqual("project", p1.name)
        p2 = p1.get_node("sub2.bbb")
        self.assertEqual("bbb", p2.name)
        a = p2.activities[0]
        self.assertEqual(date(2012, 7, 14), a.day().date)

#class EndToEnd(TestCase):
#    def test_read(self):
#        main('run -w 2012-08 example1.log'.split(' '))


class EndToEndTests(TestCase):
    def doit(self, cmdline, expected):
        ow = OutputWrapper(expected)
        do_main('run ' + cmdline)
        self.assertTrue(ow.compare())
        
    def test_1(self):
        self.doit('-s -t -w -f 2012-07 test-1.fly', 'test-1.out')
    
    def test_2(self):
        self.doit('-w -f 2012-07-14..2012-08-01 -a test-2.fly', 'test-2.out')
    
    def test_3(self):
        self.doit('-s simple-wp.fly', 'simple-wp.out')
    
    def test_4a(self):
        self.doit('-t -f week test-4.fly', 'test-4a.out')
    
    def test_4b(self):
        self.doit('-t -f week,month test-4.fly', 'test-4b.out')
    
    def test_5(self):
        self.doit('-t test-5.fly', 'test-5.out')
    
    def test_hours_minutes(self):
        self.doit('-t -w hours-minutes.fly', 'hours-minutes.out')
    
    def test_reset(self):
        self.doit('-t reset-test.fly', 'reset-test.out')
    
    def test_day_comment(self):
        self.doit('-t -C test-day-comment.fly', 'test-day-comment.out')
    
    def test_leave_holiday(self):
        self.doit('-t -C test-leave-holiday.fly', 'test-leave-holiday.out')
    
    def test_must_hours(self):
        self.doit('-t test-must-hours.fly', 'test-must-hours.out')
    
    def test_simple_self_import(self):
        self.doit('-t -C imports/self-import-1.fly', 'imports/self-import-1.out')
        
    def test_import_loop(self):
        self.doit('-b imports/import-loop-1.fly', 'imports/import-loop-1.out')
        
    def test_import_split_wp(self):
        self.doit('-s imports/wp-import-2.fly', 'imports/wp-import-2.out')
        
    def test_import_a_file(self):
        self.doit('-t -w -C imports/days-import-1.fly', 'imports/days-import-1.out')
        
    def test_import_a_file_2(self):
        self.doit('-t -w -C imports/sub/import-path-up-1.fly', 'imports/sub/import-path-up-1.out')
        
    def test_errors_in_file(self):
        self.doit('error-test.fly', 'error-test.out')
        
    def test_check_days(self):
        self.doit('-c check-days-test.fly', 'check-days-test.out')
        
    def test_block_days(self):
        self.doit('-t -C block-days-test.fly', 'block-days-test.out')
    
    def test_re_read_file(self):
        self.doit('-t -C reread-test.fly reread-test.fly', 'reread-test.out')
    
    def test_missing_file(self):
        self.doit('this-file-does-not-exist.fly', 'this-file-does-not-exist.out')
    
    def test_missing_import_file(self):
        self.doit('imports/missing-import.fly', 'imports/missing-import.out')
    
    def test_bad_filter_option(self):
        self.doit('-b -c -f bad-filter-string bad-filter-option.fly', 'bad-filter-option.out')
    
    def test_public_holiday_on_weekend(self):
        self.doit('-t public-holiday-on-weekend.fly', 'public-holiday-on-weekend.out')

    def test_bad_indent_1(self):
        self.doit('indentation/bad-1.fly', 'indentation/bad-1.out')

    def test_bad_indent_2(self):
        self.doit('indentation/bad-2.fly', 'indentation/bad-2.out')

    def test_bad_indent_3(self):
        self.doit('indentation/bad-3.fly', 'indentation/bad-3.out')

    def test_bad_indent_4(self):
        self.doit('indentation/bad-4.fly', 'indentation/bad-4.out')
        
class CalcActivitiesByMonth(TestCase):
    def test_read(self):
        self.u = Universe()
        r = Reader(self.u)
        r.read('simple-project-2.fly')
        p1 = self.u.get_workpackage("project")
        self.assertEqual("project", p1.name)
        p2 = p1.get_node("sub2.bbb")
        self.assertEqual("bbb", p2.name)
        a = p2.activities[0]
        self.assertEqual(date(2012, 7, 14), a.day().date)
        act = self.doStats(7)
        self.assertEqual(2.0, act.get_node('project.sub1.aa').value)
        self.assertEqual(3.0, act.get_node('project.sub3').value)
        self.assertEqual(10.0, act.get_node('project.sub2').value)
        act = self.doStats(8)
        self.assertEqual(1.5, act.get_node('project.sub1.aa').value)
        self.assertEqual(4.0, act.get_node('project.sub1').value)
        self.assertEqual(4.5, act.get_node('project.sub2').value)
        act = self.doStats(9)
   
    def doStats(self, month):
        ow = OutputWrapper('simple-project-2.out-' + str(month))
        act = self.u.workpackage_root.calc_activity(MonthFilter(2012, month))
        options = {'indent':'    '}
        act.dump(options)
        self.assertTrue(ow.compare())
        ow = OutputWrapper('simple-project-2.out-' + str(month) + '-act')
        options['activities'] = True
        act.dump(options)
        self.assertTrue(ow.compare())
        return act
        
if __name__ == '__main__':
    unittest.main()
