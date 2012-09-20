#!/usr/bin/python3

_version = '0.1'

_copyright = \
'''
  TimeFlies v. {0:s} is a time log and work package processor.
    
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

from datetime import date
import re
import weakref
import sys
import getopt

def make_date(dstr):
    '''
    Create a date object out of a string of the form YYYY-MM-DD and return it.
    '''
    year, month, day = dstr.split('-')
    return date(int(year), int(month), int(day))

def is_weekend(d):
    '''
    Return True if the given date is a Saturday or a Sunday, False otherwise.
    '''
    return d.isoweekday() == 6 or d.isoweekday() == 7

def format_floatval(val, what):
    if val == 0.0:
        return '--.-- ' + what
    else:
        return '{0:5.2f} '.format(val) + what

class AllFilter:
    def passes(self, day):
        return True
    
class MonthFilter:
    def __init__(self, year, month):
        self.year = year
        self.month = month
    
    def passes(self, day):
        return day.date.year == self.year and day.date.month == self.month

def make_filter(arg):
    if arg == 'all':
        return AllFilter()
    else:
        year, month = arg.split('-')
        return MonthFilter(int(year), int(month))

class Node:
    def __init__(self):
        self._parent = None
        self._children = None
        self._children_byname = None

    def add_child(self, node):
        if self._children_byname == None:
            self._children = []
            self._children_byname = {}
        
        name = node.get_name()
        
        if name in self._children_byname:
            idx = self._children_byname[name]
            self._children[idx]._parent = None
            self._children[idx] = node
        else:
            idx = len(self._children)
            self._children.append(node)
            self._children_byname[name] = idx
            
        node._parent = weakref.ref(self)
    
    def has_child(self, chld):
        if self._children_byname == None:
            return False
        elif isinstance(chld, int):
            return 0 <= chld and chld < len(self._children)
        else:
            return chld in self._children_byname
    
    def get_child(self, chld):
        if not self.has_child(chld):
            return None
        elif isinstance(chld, int):
            return self._children[chld]
        else:
            return self._children[self._children_byname[chld]]
    
    def get_node(self, pathstr, create=False):
        path = pathstr.split('.')
        n = self
        for c in path:
            if n.has_child(c):
                n = n.get_child(c)
            else:
                if not create:
                    return None
                else:
                    newnode = self.create_node(c)
                    n.add_child(newnode)
                    n = newnode
        return n

    def dump(self, options, indent=''):
        self.dump_node(options, indent)
        if self._children != None:
            indent += options['indent']
            for c in self._children:
                c.dump(options, indent)
    
    def create_node(self, name):
        pass

    def dump_node(self, options, indent):
        pass
    
    def get_name(self):
        pass
    
def dump_activities(activities, indent, options):
    indent += options['indent']
    
    for a in activities:
        comment = (', ' + a.description) if a.description != None else ''
        print(indent + '@ ' + str(a.day().date) + ' ' + str(a.duration) + comment)

class ValueNode(Node):
    def __init__(self, workpackage, value=None):
        Node.__init__(self)
        self.value = value
        self.workpackage = workpackage
        self.activities = []
    
    def get_name(self):
        return self.workpackage.name
    
    def add_activity(self, activity):
        self.activities.append(activity)

    def dump_node(self, options, indent):
        desc = self.workpackage.description
        adorneddesc = (' -- ' + desc) if desc != None else ''
        print('{1:s}{0:6.2f} : {2:s}{3:s}'.format(self.value, indent, self.get_name(), adorneddesc))
        
        if 'activities' in options:
            dump_activities(self.activities, '         ' + indent, options)
 
class WorkPackage(Node):
    def __init__(self, name, desc=None, effort=0):
        Node.__init__(self)
        self.name = name
        self.description = desc
        self.effort = int(effort)
        self.activities = []
    
    def create_node(self, name):
        return WorkPackage(name)
    
    def get_name(self):
        return self.name
    
    def calc_effort(self):
        e = self.effort
        for s in self._children:
            e += s.calc_effort()
        return e
    
    def calc_activity(self, dayfilter):
        res = ValueNode(self)
        totals = 0.0
        for a in self.activities:
            if dayfilter.passes(a.day()):
                totals += a.duration
                res.add_activity(a)

        if totals != 0.0 and self._children != None:
            res.add_child(ValueNode('--self--', totals))
        
        if self._children != None:
            for s in self._children:
                c = s.calc_activity(dayfilter)
                if c.value != 0.0:
                    totals += c.value
                    res.add_child(c)
        
        res.value = totals
            
        return res
        
    def add_activity(self, activity):
        self.activities.append(activity)
        activity.workpackage = weakref.ref(self)

    def dump_node(self, options, indent):
        desc = (' -- ' + self.description) if self.description != None else ''        
        print(indent + self.name + desc)
        
        if 'activities' in options:
            dump_activities(self.activities, indent, options)

class Activity:
    def __init__(self, duration, description):
        self.day = None
        self.workpackage = None
        self.duration = float(duration)
        self.description = description
        
class Day:
    """A Day object represents a day of work. It has a date,
    hour information and comment information attached to it."""
    def __init__(self, dt):
        if isinstance(dt, str):
            self.date = make_date(dt)
        elif isinstance(dt, date):
            self.date = dt
        else:
            self.date = None
        self.directives = None
        self.start = 0
        self.stop = 0
        self.off = 0
        self.ill = 0
        self.leave = 0
        self.phol = False
        self.comments = []
        self.activities = []
        
    def add_directive(self, d):
        if self.directives == None:
            self.directives = [ d ]
        else:
            self.directives.append(d)
    
    def add_activity(self, activity):
        self.activities.append(activity)
        activity.day = weakref.ref(self)
        
    def add_comment(self, comment):
        self.comments.append(comment)

    def add_off(self, off):
        self.off += off

    def set_phol(self, phol):
        self.phol = phol

    def add_leave(self, leave):
        self.leave += leave

    def add_ill(self, ill):
        self.ill = ill

    def set_hours(self, start, stop):
        self.start = start
        self.stop = stop

    def calc_activity(self):
        totals = 0.0
        for a in self.activities:
            totals += a.duration
        return totals
        
    def calc_balance(self):
        return self.calc_worked() + self.ill + self.leave

    def calc_worked(self):
        return self.stop - self.start - self.off
    
    def calc_required(self):
        if self.phol or is_weekend(self.date):
            return 0.0
        else:
            return 8.0
    
    def dump(self):
        print(self.date.strftime('%Y-%m-%d, %a: ') + \
              format_floatval(self.calc_worked(), "worked") + ', ' +\
              format_floatval(self.leave, "leave") + ', ' +\
              format_floatval(self.ill, "ill"))

        
class Directive:
    def __init__(self):
        self.reset = False
        self.leave = None
        self.must = None
        self.have = None

    def set_leave(self, leave):
        self.leave = leave
        return self
    
    def set_must(self, must):
        self.must = must
        return self
    
    def set_have(self, have):
        self.have = have
        return self
    
    def set_reset(self):
        self.reset = True
        return self

class Universe:
    def __init__(self):
        self.days = {}
        self.workpackage_root = WorkPackage("ALL")
    
    def get_workpackage(self, pathname):
        return self.workpackage_root.get_node(pathname)
        
    def get_chrono_days(self):
        return sorted(self.days.values(), key = lambda day: day.date)
    
class WorkPackageLineBookmark:
    def __init__(self, workpackage, indent, parent=None):
        self.indent = indent
        self.workpackage = workpackage
        self.parent = parent

class Reader:
    def __init__(self, uni):
        self._universe = uni
        self._inputfile = None
        self._linecount = 0
        self._currentday = None

    def read(self, inputfile):
        self._inputfile = inputfile
        f = open(inputfile)
        self._linecount = 0
        self._currentday = None
        self._reset_workpackage_stack()
        
        for line in f:
            self._linecount += 1
            line = re.sub(" *#.*", "", line).rstrip()
            
            if line == '':
                self._reset_workpackage_stack()
            elif self._in_workpackage_definition():
                self._process_workpackage(line)
            elif line.startswith('wp '):
                self._process_workpackage(line[3:].strip())
            elif line.startswith('work-package '):
                self._process_workpackage(line[13:].strip())
            else:
                self._reset_workpackage_stack()
                    
                if line.startswith('- '):
                    self._process_activity(line[2:].strip())
                elif line.startswith('-- '):
                    self._process_comment(line[3:].strip())
                elif line.startswith('todo '):
                    if not self._currentday == None:
                        self._msg('WARNING: TO DO item found beyond the beginning of the file')
                    else:
                        self._msg('TO DO: ' + line[5:].strip())
                elif line.strip() != '':
                    self._process_instructions(line)
        f.close()
        
    def _msg(self, text):
        print(self._inputfile + ':' + str(self._linecount) + ': ERROR : ' + text)
        
    def _reset_workpackage_stack(self):
        self._workpackage_stack = WorkPackageLineBookmark(self._universe.workpackage_root, -1)

    def _in_workpackage_definition(self):
        return self._universe.workpackage_root != self._workpackage_stack.workpackage
    
    #   name.of.the.workpackage [params ...], description
    def _process_workpackage(self, line):
        items = line.split(',', 1)
        spec = items[0].strip().split(' ')
        fullname = spec[0]
                
        indent = len(line) - len(line.lstrip())
        
        while indent <= self._workpackage_stack.indent:
            self._workpackage_stack = self._workpackage_stack.parent
        
        wp = self._workpackage_stack.workpackage.get_node(fullname, create=True)
        
        if len(spec) > 1: # effort
            wp.effort = spec[1]
            
        if len(items) == 2: # description
            wp.description = items[1].strip()
        
        self._workpackage_stack = WorkPackageLineBookmark(wp, indent, self._workpackage_stack)
        
    def _process_activity(self, line):
        comps = line.split(',', 1)
        args = comps[0].strip().split(' ')
        if len(args) < 2:
            self._msg('an activity must have a work package and a duration.')
        else:
            workpackage_name = args[0]
            duration = args[1]
            if len(comps) == 2:
                desc = comps[1].strip()
            else:
                desc = None

            try:
                activity = Activity(duration, desc)
                wp = self._universe.get_workpackage(workpackage_name)
                if wp == None:
                    self._msg('invalid activity work package ' + workpackage_name
                             + ' on day ' + str(self._currentday.date))
                else:
                    wp.add_activity(activity)
                    self._currentday.add_activity(activity)
            except ValueError:
                self._msg('invalid activity duration ' + duration + '.')
            
        
    def _process_comment(self, comment):
        self._currentday.add_comment(comment)

    def _process_instructions(self, line):
        morsels = line.split(',')
        for mors in morsels:
            self._process_instruction(mors.strip())

    def _add_leave(self, start, end, where):
        st = make_date(start)
        end = make_date(end)

        d = st.toordinal()
        end = end.toordinal()

        while d <= end:
            dt = date.fromordinal(d)

            if not is_weekend(dt):
                self._new_day(str(dt))
                self._currentday.add_leave(8.0)
                self._currentday.add_comment('leave: ' + where)

            d = d + 1

    def _new_day(self, datestring):
        if datestring in self._universe.days:
            self._currentday = self._universe.days[datestring]
        else:
            self._currentday = Day(datestring)
            self._universe.days[datestring] = self._currentday

    def _process_instruction(self, argliststring):
        arglist = argliststring.split(' ')
        instr = arglist[0]
        args = arglist[1:]

        if instr == 'day':
            self._new_day(args[0])
            return
        
        if instr == 'leave' and len(args) == 3:
            self._add_leave(args[0], args[1], args[2])
            return
        
        if self._currentday == None:
            self._msg('No current day for instruction <' + argliststring + '>.')
            return
        
        if instr == 'reset':
            self._currentday.add_directive(Directive().set_reset())
        elif instr == 'add-leave':
            self._currentday.add_directive(Directive().set_leave(float(args[0])))
        elif instr == 'balance-must':
            self._currentday.add_directive(Directive().set_must(float(args[0])))
        elif instr == 'balance-have':
            self._currentday.add_directive(Directive().set_have(float(args[0])))
        elif instr == 'off':
            self._currentday.add_off(float(args[0]))
        elif instr == 'hours':
            self._currentday.set_hours(float(args[0]), float(args[1]))
        elif instr == 'leave':
            if len(args) == 2:
                self._currentday.add_leave(float(args[0]))
                self._currentday.add_comment('leave: ' + args[1])
            else:
                self._msg('Weird leave spec <' + argliststring + '>.')
        else:
            self._msg('Weird instruction <' + argliststring + '>.')

class Status:
    def __init__(self, name):
        self.name = name
        self.reset()

    def reset(self):
        self._musthours = 0
        self._havehours = 0
        self._leavebalancehours = 0
        self._leavetakenhours = 0
        self._illhours = 0
        self._workedhours = 0

    def increase_must_hours(self, dt):
        # public holidays?
        workday = not is_weekend(dt)
        if workday:
            self._musthours += 8
        return workday
    
    def process_day(self, day):
        if day.directives != None:
            for di in day.directives:
                self._process_directive(di)

        self._musthours += day.calc_required()
        self._havehours += day.calc_balance()
        self._workedhours += day.calc_worked()
        self._illhours += day.ill
        self._leavebalancehours -= day.leave
        self._leavetakenhours += day.leave
        
    def _process_directive(self, di):
        if di.reset:
            self.dump()
            self.reset()
            #print('--- reset ' + self.name + '---')
        elif di.leave != None:
            self._leavebalancehours += di.leave
        elif di.must != None:
            self._musthours = di.must
        elif di.have != None:
            self._havehours = di.have
        
    def dump(self):
        print(self.name + ': must = {0:6.2f}, worked = {1:6.2f}, ill = {2:6.2f}, leave taken= {3:6.2f}, leave left = {4:6.2f}, have = {5:6.2f}'\
              .format(self._musthours, self._workedhours, self._illhours, self._leavetakenhours, self._leavebalancehours, self._havehours))

class Statistics:
    def __init__(self, universe):
        self.days = universe.get_chrono_days()
        self.globalbalance = Status('global')
        self.weeklybalance = Status('weekly')
        self.previous = None

    def _process_gap(self, d1, dayfilter):
        if self.previous == None:
            return

        d = self.previous.date.toordinal() + 1
        end = d1.date.toordinal()

        while d < end:
            dt = date.fromordinal(d)
            if dayfilter.passes(Day(dt)) and self.globalbalance.increase_must_hours(dt):
                print('missing weekday record for ' + str(dt))
            d = d + 1

    def check_days(self, dayfilter):
        for d in self.days:
            if dayfilter.passes(d):
                worked = d.calc_worked()
                tasked = d.calc_activity()
                delta = tasked - worked
                if delta != 0.0:
                    print('*** {0:s} : worked = {1:5.2f}, tasked = {2:5.2f}, delta = {3:5.2f}'
                          .format(d.date.strftime('%Y-%m-%d, %a'), worked, tasked, delta))
        
    def calc_balance(self, dayfilter):
        self.previous = None
        for d in self.days:
            self._process_gap(d, dayfilter)
            if dayfilter.passes(d):
                if d.date.isoweekday() == 1:
                    self.weeklybalance.dump()
                    print()
                    self.weeklybalance.reset()
                    
                self.weeklybalance.process_day(d)
                self.globalbalance.process_day(d)
                d.dump()
                self.previous = d

        self.weeklybalance.dump()
        self.globalbalance.dump()

def show_usage(cmd):
    print()
    print('  Usage: ' + cmd + ' [options] <infile> [..]')
    print('''
  TimeFlies v. {0:s} -- Copyright (C) 2012 Joerg Bullmann (jb@heilancoo.net)

  This is a simple time log and work package tree processor. Projects can be
  defined in form of hierarchical work package trees. Daily work progress is logged
  in form of day records with attached activities referring to work packages.

  This program comes with ABSOLUTELY NO WARRANTY. This is free software,
  and you are welcome to redistribute it under certain conditions. You
  should have received a copy of the GNU General Public License along
  with this program. If not, see <http://www.gnu.org/licenses/>.

  Options:

  -h, --help : show this info
  -c, --copyright : show copyright info
  -t, --work-time <yyyy-mm> : calculate the total must/have/leave/ill
      work hour balance
  -d, --day-check <yyyy-mm> : check the daily work time vs. booked
      work package time; helps to find unaccounted for time at work
  -w, --work-packages <yyyy-mm> : calculate hours worked on work packages
      for the given month
  -s, --show-work-packages : show the work package tree
  -a, --activities : show activities in work package tree output for option -w or -s
  -i, --indentation <width> : indent each level in the work package hierarchy by
      <width> space characters; default: 4
'''.format(_version))

def main(argv):
    jobs = []
    opts, args = None, None
    dumpopts = {}
    dumpopts['indent'] = '    '
    
    try:
        opts, args = getopt.getopt(argv[1:], 'hcasi:w:d:t:',
                                   ['copyright', 'help', 'activities', 'show-work-packages',
                                    'indentation=',
                                    'work-time=', 'day-check=', 'work-packages='])

        for opt, val in opts:
            if opt == '-h' or opt == '--help':
                show_usage(argv[0])
            elif opt == '-c' or opt == '--copyright':
                print(_copyright.format(_version))
            elif opt == '-a' or opt == '--activities':
                dumpopts['activities'] = True
            elif opt == '-i' or opt == '--indentation':
                dumpopts['indent'] = ' ' * int(val)
            elif opt == '-t' or opt == '--work-time':
                jobs.append(('work-time', val))
            elif opt == '-d' or opt == '--day-check':
                jobs.append(('day-check', val))
            elif opt == '-w' or opt == '--work-packages':
                jobs.append(('work-packages', val))
            elif opt == '-s' or opt == '--show-work-packages':
                jobs.append(('show-work-packages', val))

    except getopt.GetoptError as e:
        print(argv[0] + ': ' + str(e))
        print('For help try: ' + argv[0] + ' --help')
        exit()
        
    u = Universe()
    r = Reader(u)
    for f in args:
        r.read(f)
    s = Statistics(u)
    
    for j, arg in jobs:
        if j == 'day-check':
            print('Day check (' + arg + '):')
            f = make_filter(arg)
            s.check_days(f)
        elif j == 'work-packages':
            print('Work package summary (' + arg + '):')
            f = make_filter(arg)
            act = u.workpackage_root.calc_activity(f)
            act.dump(dumpopts)
        elif j == 'work-time':
            print('Time at work overview (' + arg + '):')
            f = make_filter(arg)
            s.calc_balance(f)
        elif j == 'show-work-packages':
            print('Work package breakdown:')
            u.workpackage_root.dump(dumpopts)
        else:
            print('*** Unknown job: ' + j)
            
if __name__ == '__main__':
    main(sys.argv)





