#!/usr/bin/env python3

_version = '0.6'

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
import os.path

_outputdest = sys.stdout

def set_output_destination(dest):
    global _outputdest
    _outputdest = dest

def output(text=None, dest=None):
    if text is None:
        text = ''
    if dest is None:
        dest = _outputdest
    print(text, file=dest)

def plural(number, unit, plural='s'):
    pl = '' if number == 1 else plural   
    num = 'no' if number == 0 else str(number) 
    return num + ' ' + unit + pl

def tidy_whitespace(mess):
    '''Truncates leading and trailing white spaces and
    replaces each other sequence of white spaces by a single space.'''
    return re.sub('\s+', ' ', mess.strip())

def make_date(dstr):
    '''Create a date object out of a string of the form
    YYYY-MM-DD and return it.'''
    year, month, day = dstr.split('-')
    return date(int(year), int(month), int(day))

def make_time(tstr):
    if re.match('^\d+:\d\d$', tstr):
        hours, minutes = tstr.split(':')
        return float(hours) + (float(minutes) / 60.0)
    elif re.match('^\d+(\.\d{1,2})?$', tstr):
        return float(tstr)
    else:
        return None

day_map = { 'mon':0, 'tue':1, 'wed':2, 'thu':3, 'fri':4, 'sat':5, 'sun':6 }

def is_weekend(day):
    '''Return True if the given date is a Saturday or a Sunday,
    False otherwise.'''
    return day.weekday() == 5 or day.weekday() == 6

def format_floatval(val):
    if val == 0.0:
        return '----.--'
    else:
        return '{0:7.2f}'.format(val)

def dump_day_header():
    output('{0:^15s} {1:>7s} {2:>7s} {3:>7s} {4:>7s}'.format('when', 'worked', 'leave', 'sick', 'balance'))

class AllFilter:
    def passes(self, day):
        return True

class RangeFilter:
    def __init__(self, starty, startm, startd, endy, endm, endd):
        self._start = date(starty, startm, startd).toordinal()
        self._end = date(endy, endm, endd).toordinal()
    
    def passes(self, day):
        ordinal = day.date.toordinal()
        return self._start <= ordinal and ordinal <= self._end
        
class MonthFilter:
    def __init__(self, year, month):
        self._year = year
        self._month = month
    
    def passes(self, day):
        return day.date.year == self._year and day.date.month == self._month

def make_filter(arg):
    if arg == 'all':
        return AllFilter()
    elif re.match('^\d{4}-\d{2}$', arg):
        year, month = arg.split('-')
        return MonthFilter(int(year), int(month))
    elif re.match('^\d{4}(-\d{2}){2}\.\.\d{4}(-\d{2}){2}$', arg):
        startstring, endstring = arg.split('..')
        starty, startm, startd = startstring.split('-')
        endy, endm, endd = endstring.split('-')        
        return RangeFilter(int(starty), int(startm), int(startd),
                           int(endy), int(endm), int(endd))
    else:
        output('Bad time filter argument: ' + arg)
        return None

class Node:
    def __init__(self):
        self._parent = None
        self._children = None
        self._children_byname = None
        self.activities = None

    def add_child(self, node):
        if self._children_byname is None:
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
        if self._children_byname is None:
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
        if self._children is not None:
            indent += options['indent']
            for c in self._children:
                c.dump(options, indent)
    
    def tidy_up(self):
        if self.activities is not None:
            self.activities.sort(key=lambda a: a.day().date)
        
        if self._children is not None:
            for c in self._children:
                c.tidy_up()
        
    def create_node(self, name):
        pass

    def dump_node(self, options, indent):
        pass
    
    def get_name(self):
        pass
    
def dump_activities(activities, indent, options):
    if activities is not None:
        for a in activities:
            comment = '' if a.description is None else ('; ' + a.description)
            output(indent + '- ' + str(a.day().date) + ' ' + str(a.duration) + comment)

class ValueNode(Node):
    def __init__(self, workpackage, value=None):
        Node.__init__(self)
        self.value = value
        self.workpackage = workpackage
    
    def get_name(self):
        return '_self' if self.workpackage is None else self.workpackage.name

    def dump_node(self, options, indent):
        desc = None if self.workpackage is None else self.workpackage.description
        adorneddesc = '' if desc is None else ('; ' + desc)
        output('{0:s}{1:7.2f} : {2:s}{3:s}'
               .format(indent, self.value, self.get_name(), adorneddesc))
        
        if 'activities' in options:
            dump_activities(self.activities, '          ' + indent, options)
 
class WorkPackage(Node):
    def __init__(self, name, desc=None, effort=0):
        Node.__init__(self)
        self.name = name
        self.description = desc
        self.effort = int(effort)
    
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
        
        if self.activities is not None:
            for a in self.activities:
                if dayfilter.passes(a.day()):
                    totals += a.duration
                    a.attach_to(res)

        if self._children is not None:
            for s in self._children:
                c = s.calc_activity(dayfilter)
                if c.value != 0.0:
                    # Only attach children with actual effort to
                    # keep the result pruned nicely
                    if res.activities:
                        # wp 'self' has both activities on itself and
                        # on sub-wps. To make the activities on the wp
                        # itself more easily visible, we insert a dummy
                        # 'self' child here and move the activities
                        # in question to that one.
                        selfres = ValueNode(None, totals)
                        res.add_child(selfres)
                        for act in res.activities:
                            act.attach_to(selfres)
                        res.activities = []
                    totals += c.value
                    res.add_child(c)
        
        res.value = totals
            
        return res

    def dump_node(self, options, indent):
        desc = '' if self.description is None else ('; ' + self.description)        
        output(indent + self.name + desc)
        
        if 'activities' in options:
            dump_activities(self.activities, indent, options)

class Activity:
    def __init__(self, duration, description):
        self.day = None
        self.workpackage = None
        self.duration = float(duration)
        self.description = description
    
    def attach_to(self, node):
        '''Attaches ourselves to the given node. If the node is a
        WorkPackage or a Day, a weak-ref to the parent node is
        set.'''
        if isinstance(node, WorkPackage):
            self.workpackage = weakref.ref(node)
        elif isinstance(node, Day):
            self.day = weakref.ref(node)
        
        if node.activities is None:
            node.activities = [ self ]
        else:
            node.activities.append(self)

def add_value(original, newVal, newDesc):
    if isinstance(original, tuple):
        v, d = original
    else:
        v = original
        d = None

    v += newVal
    
    if newDesc is not None:
        d = newDesc if d is None else d + '; ' + newDesc        
    
    if d is not None:
        return (v, d)
    else:
        return v

def set_value(original, val, comment=None):
    if comment is not None:
        return (val, comment)
    else:
        if isinstance(original, tuple):
            return (val, original[1])
        else:
            return val

def get_value(value):
    if isinstance(value, tuple):
        return value[0]
    else:
        return value

def get_desc(value):
    if isinstance(value, tuple):
        return value[1]
    else:
        return None

class Day:
    '''A Day object represents a day of work. It has a date,
    hour information and comment information attached to it.'''
    def __init__(self, dt):
        if isinstance(dt, str):
            self.date = make_date(dt)
        elif isinstance(dt, date):
            self.date = dt
        else:
            self.date = None
        self.musthours = None
        self.directives = None
        self.start = None
        self.stop = None
        self.off = 0.0
        self.sick = 0.0
        self.leave = 0.0
        self.required = 0.0 if is_weekend(self.date) else 8.0
        self.phol = None
        self.comments = None
        self.activities = None
        
    def add_directive(self, d):
        if self.directives is None:
            self.directives = [ d ]
        else:
            self.directives.append(d)
        
    def add_comment(self, comment):
        if comment is not None:
            if self.comments is None:
                self.comments = [ comment ]
            else:
                self.comments.append(comment)

    def add_off(self, off, comment=None):
        self.off = add_value(self.off, off, comment)

    def set_phol(self, comment):
        self.phol = 'public holiday' if comment is None else comment 

    def add_leave(self, leave, comment=None):
        if isinstance(leave, bool):
            self.leave = set_value(self.leave, leave, comment)
        else:
            self.leave = add_value(self.leave, leave, comment)

    def add_sick(self, sick, comment=None):
        if isinstance(sick, bool):
            self.sick = set_value(self.sick, sick, comment)
        else:
            self.sick = add_value(self.sick, sick, comment)

    def set_hours(self, start, stop):
        if self.start is not None or self.stop is not None:
            return False
        self.start = start
        self.stop = stop
        return True
    
    def calc_activity(self):
        totals = 0.0
        if self.activities is not None:
            for a in self.activities:
                totals += a.duration
        return totals
        
    def calc_have(self):
        return self.calc_worked() + get_value(self.sick) + get_value(self.leave)

    def calc_worked(self):
        at_work = 0.0 if self.start is None or self.stop is None else self.stop - self.start
        return at_work - get_value(self.off)
    
    def calc_required(self):
        return 0.0 if self.phol else self.required

    def calc_balance(self):
        return self.calc_have() - self.calc_required()
    
    def is_workday(self):
        return self.required != 0.0
                    
    def dump(self, options):
        worked = self.calc_worked()
        cmnt = ''
        
        for s in self.phol, get_desc(self.leave), get_desc(self.sick), get_desc(self.off):
            if s is not None:
                cmnt = cmnt + '; ' + s
            
        output(self.date.strftime('%Y-%m-%d %a: ') + \
              format_floatval(worked) + ' ' +\
              format_floatval(get_value(self.leave)) + ' ' +\
              format_floatval(get_value(self.sick)) + ' ' +\
              format_floatval(self.calc_balance()) + cmnt[1:])
        
        if 'comments' in options and self.comments is not None:
            prefix = ' ' * 14 + '; '
            for cmnt in self.comments:
                output(prefix + cmnt)

        
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
        self.dump_options = { 'indent':'    ' }
        self.inputfiles = []
        self.inputfileset = set()
        self.currentday = None
        self.musthours = None
        self.errors = 0
        self.warnings = 0
        
    def remember(self, file):
        if file in self.inputfileset:
            return True
        else:
            self.inputfileset.add(file)
            return False
        
    def add_file(self, file):
        self.inputfiles.append(file)
    
    def get_workpackage(self, pathname):
        return self.workpackage_root.get_node(pathname)
        
    def get_chrono_days(self):
        return sorted(self.days.values(), key = lambda day: day.date)
    
    def bill_of_materials(self, abspaths=False):
        for file in self.inputfiles:
            if abspaths:
                indent_len = len(file) - len(file.lstrip())
                f = file[:indent_len] + os.path.abspath(file[indent_len:]) 
            else:
                f = file
            output(f)
        output(plural(len(self.inputfiles), 'file') + ' processed.')

    def tidy_up(self):
        self.currentday = None

        if self.musthours is None:
            self.musthours = [8.0] * 5 + [0.0] * 2     
   
        must_hours = self.musthours
            
        for day in self.get_chrono_days():
            if day.musthours is not None:
                must_hours = day.musthours
            
            day.required = must_hours[day.date.weekday()]

            if day.phol is not None:
                day.leave = 0.0
                day.sick = 0.0
            
            leave = get_value(day.leave)
            sick = get_value(day.sick)
            
            if isinstance(leave, bool) and leave == True:
                day.leave = set_value(day.leave, day.required)
            if isinstance(sick, bool) and sick == True:
                day.sick = set_value(day.sick, day.required)
        
        self.workpackage_root.tidy_up()
        
class WorkPackageLineBookmark:
    def __init__(self, workpackage, indent, parent=None):
        self.indent = indent
        self.workpackage = workpackage
        self.parent = parent

class Reader:
    def __init__(self, uni, parent=None):
        self._universe = uni
        self._parent = parent

    def read(self, inputfile):
        self._absinputfile = os.path.abspath(inputfile)
        self._already_read_before = self._universe.remember(self._absinputfile)
        self._inputfile = inputfile
        self._linecount = 0
        self._reset_workpackage_stack()
        
        if self._have_import_loop():
            self._parent._msg('file ' + inputfile + ' already processed', 'WARNING')
            return
        
        try:
            with open(inputfile) as f:
                bom_indent = self._universe.dump_options['indent'] * self._import_level()
                self._universe.add_file(bom_indent + inputfile)
                self._read_file(f)
            
        except IOError as e:
            msg = 'failed to open file; ' + str(e)
            if self._parent is None:
                output(msg)
            else:
                self._parent._msg(msg)
        
        if self._parent is None: # top level read finished
            self._universe.tidy_up()
            msg = ''
            if self._universe.errors > 0:
                msg += ", " + plural(self._universe.errors, "error")
            if self._universe.warnings > 0:
                msg += ", " + plural(self._universe.warnings, "warning")
            if len(msg) > 0:
                output(msg[2:] + '.')

    def _import_level(self):
        reader, lev = self, 0
        while reader._parent is not None:
            reader, lev = reader._parent, lev + 1
        return lev
            
    def _read_file(self, f):
        for line in f:
            self._linecount += 1
            line = re.sub(" *#.*", "", line).rstrip()
            
            indent = len(line) - len(line.lstrip())
            
            if indent == 0:
                self._reset_workpackage_stack()
                
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
                elif line.startswith('; '):
                    self._process_comment(line[2:].strip())
                elif line.startswith('import '):
                    self._import_file(line[7:].strip())
                elif line.strip() != '':
                    self._process_instructions(line)
        
    def _have_import_loop(self):
        p = self._parent
        
        while p is not None:
            if p._absinputfile == self._absinputfile:
                return True
            p = p._parent
            
        return False
    
    def _import_file(self, file):
        sub_reader = Reader(self._universe, self)
        
        if os.path.isabs(file):
            f = file
        else:
            folder = os.path.dirname(self._inputfile)
            f = os.path.join(folder, file)
        
        sub_reader.read(f)

    def _msg_redef(self, text):
        self._msg('re-defining ' + text + ' (this file has already been read before)')
        
    def _msg(self, text, kind='ERROR'):
        output(self._inputfile + ':' + str(self._linecount) + ': ' + kind + ' : ' + text)
        parent = self._parent
        
        while parent is not None:
            output(parent._inputfile + ':' + str(parent._linecount) + ': imported here')
            parent = parent._parent
        
        if kind == 'ERROR':
            self._universe.errors += 1
        elif kind == 'WARNING':
            self._universe.warnings += 1
        else:
            output('*** Bad msg type ' + kind)
            
    def _reset_workpackage_stack(self):
        self._workpackage_stack = WorkPackageLineBookmark(self._universe.workpackage_root, -1)
        self._previous_indentation_prefix = ''
        
    def _in_workpackage_definition(self):
        return self._universe.workpackage_root != self._workpackage_stack.workpackage
    
    #   name.of.the.workpackage [params ...]; description
    def _process_workpackage(self, line):
        items = line.split(';', 1)
        spec = items[0].strip().split(' ')
        fullname = spec[0]
                
        indentation_len = len(line) - len(line.lstrip())
        indentation_prefix = line[:indentation_len]
        
        if ' ' in indentation_prefix and '\t' in indentation_prefix:
            self._msg('indentation contains both spaces and tabs')
            return
        
        if not indentation_prefix.startswith(self._previous_indentation_prefix) \
            and not self._previous_indentation_prefix.startswith(indentation_prefix):
            self._msg('work package indentation error')
            return
        
        self._previous_indentation_prefix = indentation_prefix
        
        while indentation_len <= self._workpackage_stack.indent:
            self._workpackage_stack = self._workpackage_stack.parent
        
        wp = self._workpackage_stack.workpackage.get_node(fullname, create=True)
        
        if len(spec) > 1: # effort
            wp.effort = make_time(spec[1])
            
        if len(items) == 2: # description
            wp.description = items[1].strip()
        
        self._workpackage_stack = WorkPackageLineBookmark(wp, indentation_len, self._workpackage_stack)
        
    def _process_activity(self, line):
        comps = line.split(';', 1)
        args = tidy_whitespace(comps[0]).split(' ')
        if len(args) < 2:
            self._msg('an activity must have a work package and a duration.')
        elif self._already_read_before:
            self._msg_redef('activity')
        else:
            workpackage_name = args[0]
            duration = args[1]
            if len(comps) == 2:
                desc = comps[1].strip()
            else:
                desc = None

            duration_float = make_time(duration)
            wp = self._universe.get_workpackage(workpackage_name)
            
            if wp is None:
                self._msg('invalid activity work package "' + workpackage_name + '".')  

            if duration_float is None:
                self._msg('invalid activity duration "' + duration + '".')
            
            if wp is not None and duration_float is not None:
                activity = Activity(duration_float, desc)
                activity.attach_to(wp)
                activity.attach_to(self._universe.currentday)
        
    def _process_comment(self, comment):
        self._universe.currentday.add_comment(comment)

    def _process_instructions(self, line):
        # Get the comment part of the line, if there is any
        instructions, semicolon, rawcomment = line.partition(';')
        comment = None if semicolon == '' else rawcomment.strip()
        
        morsels = instructions.split(',')
        for mors in morsels[:-1]:
            self._process_instruction(tidy_whitespace(mors))
        
        self._process_instruction(tidy_whitespace(morsels[-1]), comment)

    def _add_block(self, day_setter, start, end, comment):
        st = make_date(start)
        end = make_date(end)

        d = st.toordinal()
        end = end.toordinal()
        
        current_saved = self._universe.currentday
        
        while d <= end:
            dt = date.fromordinal(d)
            self._new_day([str(dt)])
            day_setter(self._universe.currentday, comment)
            d = d + 1

        self._universe.currentday = current_saved
        
    def _new_day(self, args):
        largs = len(args)
        if largs != 1 and largs != 3:
            self._msg('unexpected day argument list: "' + ' '.join(args) + '".')
            
        datestring = args[0]
        
        if datestring in self._universe.days:
            self._universe.currentday = self._universe.days[datestring]
        else:
            self._universe.currentday = Day(datestring)
            self._universe.days[datestring] = self._universe.currentday

        if largs == 3:
            start = make_time(args[1])
            end = make_time(args[2])

            if start is None:
                self._msg('bad start time argument "' + args[1] + '" in day spec.')
            elif end is None:
                self._msg('bad end time argument "' + args[2] + '" in day spec.')
            elif self._already_read_before:
                self._msg_redef('day')
            elif not self._universe.currentday.set_hours(start, end): 
                self._msg('day ' + str(self._universe.currentday.date) + ' redefined.')             

    def _make_weekday(self, day):
        if not day in day_map:
            self._msg('unknown day "' + day + '".')
            return None
        else:
            return day_map[day]
        
    def _process_must_hours(self, args):
        must_hours = [0.0] * 7
        
        for arg in args:
            day, equals, hours = arg.partition('=')
            
            if equals != '=':
                self._msg('bad must-hours argument "' + arg + '".')
            else:
                first, dots, last = day.partition('..')
                
                if dots == '..':
                    first_day = self._make_weekday(first)
                    last_day = self._make_weekday(last)
                else:
                    first_day = self._make_weekday(day)
                    last_day = first_day
                
                if first_day == None or last_day == None:
                    pass
                elif last_day < first_day:
                    self._msg('bad must-hours day range "' + day + '".')
                else:
                    hrs = make_time(hours)

                    if hrs is None:
                        self._msg('bad time duration "' + hours + '" ("' + day + '").')
                    else:
                        for d in range(first_day, last_day + 1):
                            must_hours[d] = make_time(hours)
    
        if self._universe.currentday is None:
            self._universe.musthours = must_hours
        else:
            self._universe.currentday.musthours = must_hours

    def _current_day_ok(self, args):
        currday_ok = self._universe.currentday is not None
        if not currday_ok:
            self._msg('no current day for instruction "' + ' '.join(args) + '".')
        return currday_ok
    
    def _set_time(self, args, comment, setter, default_ok=False):
        if self._current_day_ok(args):
            if len(args) == 1:
                if default_ok:
                    tm = True
                else:
                    self._msg('argument missing in instruction "' + ' '.join(args) + '".')
                    return
            elif len(args) == 2:
                tm = make_time(args[1])
            else:
                self._msg('too many arguments in instruction "' + ' '.join(args) + '".')
                return
            
            if tm is None:
                self._msg('bad time "' + args[1] + '" in instruction "' + ' '.join(args) + '".')
            else:
                setter(self._universe.currentday, tm, comment)
    
    def _process_instruction(self, argliststring, comment=None):
        arglist = argliststring.split(' ')
        instr = arglist[0]
        args = arglist[1:]

        if instr == 'day':
            self._new_day(args)
            return
        
        if instr == 'leave-days':
            self._add_block(lambda day, cmnt: day.add_leave(True, cmnt), args[0], args[1], comment)
            return
        
        if instr == 'sick-days':
            self._add_block(lambda day, cmnt: day.add_sick(True, cmnt), args[0], args[1], comment)
            return
        
        if instr == 'must-hours':
            self._process_must_hours(args)
            return

        currday = self._universe.currentday

        if instr == 'phol' or instr == 'public-holiday':
            if self._current_day_ok(arglist):
                currday.set_phol(comment)
        else:
            if self._already_read_before:
                self._msg_redef(instr)
            elif instr == 'reset':
                if self._current_day_ok(arglist):
                    currday.add_directive(Directive().set_reset())
            elif instr == 'add-leave':
                if self._current_day_ok(arglist):
                    currday.add_directive(Directive().set_leave(make_time(args[0])))
            elif instr == 'balance-must':
                if self._current_day_ok(arglist):
                    currday.add_directive(Directive().set_must(make_time(args[0])))
            elif instr == 'balance-have':
                if self._current_day_ok(arglist):
                    currday.add_directive(Directive().set_have(make_time(args[0])))
            elif instr == 'off':
                self._set_time(arglist, comment, lambda day, tm, cmnt: day.add_off(tm, cmnt))
            elif instr == 'sick':
                self._set_time(arglist, comment, lambda day, tm, cmnt: day.add_sick(tm, cmnt), True)
            elif instr == 'leave':
                self._set_time(arglist, comment, lambda day, tm, cmnt: day.add_leave(tm, cmnt), True)
            else:
                self._msg('weird instruction "' + argliststring + '".')

class Status:
    def __init__(self, name):
        self.name = name
        self.reset()

    def reset(self):
        self._musthours = 0
        self._balancehours = 0
        self._leavebalancehours = 0
        self._leavetakenhours = 0
        self._sickhours = 0
        self._workedhours = 0

    def increase_must_hours(self, dt):
        # public holidays?
        workday = not is_weekend(dt)
        if workday:
            self._musthours += 8
        return workday
    
    def process_day(self, day):
        if day.directives is not None:
            for di in day.directives:
                self._process_directive(di)

        self._musthours += day.calc_required()
        self._balancehours += day.calc_balance()
        self._workedhours += day.calc_worked()
        self._sickhours += get_value(day.sick)
        self._leavebalancehours -= get_value(day.leave)
        self._leavetakenhours += get_value(day.leave)
        
    def _process_directive(self, di):
        if di.reset:
            self.dump('reset')
            self.reset()
        elif di.leave is not None:
            self._leavebalancehours += di.leave
        elif di.must is not None:
            self._musthours = di.must
        elif di.have is not None:
            self._havehours = di.have
        
    def dump(self, tag):
        if tag is None:
            prefix = self.name
        else:
            prefix = self.name + ' ' + tag
            
        output('{0:>14s}: '.format(prefix) +\
              format_floatval(self._workedhours) + ' ' +\
              format_floatval(self._leavetakenhours) + ' ' +\
              format_floatval(self._sickhours) + ' ' +\
              format_floatval(self._balancehours))
    
class Statistics:
    def __init__(self, universe):
        self.days = universe.get_chrono_days()
        self.totals = Status('total')
        self.weekly = Status('week')
        self.monthly = Status('month')
        self.prev_day = None

    def _process_gap(self, d1, dayfilter):
        if self.prev_day is None:
            return

        d = self.prev_day.date.toordinal() + 1
        end = d1.date.toordinal()

        while d < end:
            dt = date.fromordinal(d)
            if dayfilter.passes(Day(dt)) and self.totals.increase_must_hours(dt):
                output('missing weekday record for ' + str(dt))
            d = d + 1

    def check_days(self, dayfilter):
        warnings = 0
        for d in self.days:
            if dayfilter.passes(d):
                dt_str = d.date.strftime('%Y-%m-%d %a')

                worked = d.calc_worked()
                allocated = d.calc_activity()
                delta = allocated - worked
                
                if delta != 0.0:
                    warnings += 1
                    output('{0:s}: worked {1:5.2f}, allocated {2:5.2f}, delta {3:5.2f}'
                          .format(dt_str, worked, allocated, delta))

                sick = get_value(d.sick)
                leave = get_value(d.leave)
                more_sick = sick > d.required
                more_leave = leave > d.required
                
                if more_sick:
                    output(dt_str + ': more sick time ('
                            + str(sick) + ') taken than required working time ('
                            + str(d.required) + ').')
                    warnings += 1
                
                if more_leave:
                    output(dt_str + ': more leave time ('
                            + str(leave) + ') taken than required working time ('
                            + str(d.required) + ').')
                    warnings += 1
                
                if (not more_leave) and (not more_sick) and sick + leave > d.required:
                    output(dt_str + ': more leave and sick time ('
                            + str(leave + sick) + ') taken than required working time ('
                            + str(d.required) + ').')
                    warnings += 1

        if warnings != 0:
            output(plural(warnings, 'problem') + ' detected.')
        else:
            output('ok.')
        
    def calc_balance(self, options):
        dayfilter = options['time']
        do_daily = options['day']
        do_weekly = options['week']
        do_monthly = options['month']
        self.prev_month = None
        self.prev_week = None
        self.prev_day = None
        
        dump_day_header()
        
        for d in self.days:
            self._process_gap(d, dayfilter)
            if dayfilter.passes(d):
                year, week = d.date.isocalendar()[0:2]
                this_month = str(year) + '-{0:02d}'.format(int(d.date.month))
                this_week = str(year) + '-{0:02d}'.format(int(week))
                if self.prev_day is not None:
                    if do_weekly and this_week != self.prev_week:
                        self.weekly.dump(self.prev_week)
                        self.weekly.reset()
                    if do_monthly and this_month != self.prev_month:
                        self.monthly.dump(self.prev_month)
                        self.monthly.reset()
                    
                self.weekly.process_day(d)
                self.monthly.process_day(d)
                self.totals.process_day(d)

                if do_daily and (d.calc_have() > 0.0 or d.is_workday()):
                    d.dump(options)

                self.prev_day = d
                self.prev_week = this_week
                self.prev_month = this_month

        if do_weekly:
            self.weekly.dump(self.prev_week)
        if do_monthly:
            self.monthly.dump(self.prev_month)
        self.totals.dump(None)
        
        dump_day_header()

class Application:
    def __init__(self):
        self._universe = Universe()
        self._jobs = []
        self._filter = 'all'
        self._args = None
    
    def _set_dump_option(self, key, value):
        self._dump_options()[key] = value
    
    def _get_dump_option(self, key):
        return self._dump_options()[key]
    
    def _dump_options(self):
        return self._universe.dump_options
    
    def interpret_cmdline(self, argv):
        try:
            opts, self._args = getopt.getopt(argv[1:], 'hf:tcwsaCi:b',
                                       ['help', 'version', 'copyright', 'filter=',
                                        'tally-days', 'check-days',
                                        'work-packages', 'show-work-packages',
                                        'activities', 'comments',
                                        'indent=', 'bill-of-materials'])
    
            for opt, val in opts:
                if opt == '-h' or opt == '--help':
                    self.show_usage(argv[0])
                elif opt == '--copyright':
                    output(_copyright.format(_version))
                elif opt == '--version':
                    output(_version)
                elif opt == '-f' or opt == '--filter':
                    self._filter = val
                elif opt == '-t' or opt == '--tally-days':
                    self._jobs.append('tally-days')
                elif opt == '-c' or opt == '--check-days':
                    self._jobs.append('check-days')
                elif opt == '-w' or opt == '--work-packages':
                    self._jobs.append('work-packages')
                elif opt == '-s' or opt == '--show-work-packages':
                    self._jobs.append('show-work-packages')
                elif opt == '-b' or opt == '--bill-of-materials':
                    self._jobs.append('bill-of-materials')
                elif opt == '-a' or opt == '--activities':
                    self._set_dump_option('activities', True)
                elif opt == '-C' or opt == '--comments':
                    self._set_dump_option('comments', True)
                elif opt == '-i' or opt == '--indent':
                    self._set_dump_option('indent', ' ' * int(val))
    
        except getopt.GetoptError as e:
            output(argv[0] + ': ' + str(e))
            output('For help try: ' + argv[0] + ' --help')
            exit()
        
    def read_files(self):
        r = Reader(self._universe)
        for f in self._args:
            r.read(f)
    
    def _process_filter(self):
        stats_day = False
        stats_week = False
        stats_month = False
        
        for flt in self._filter.split(','):
            if flt == 'day':
                stats_day = True
            elif flt == 'week':
                stats_week = True
            elif flt == 'month':
                stats_month = True
            else:
                tf = make_filter(flt)
                if tf is not None:
                    self._set_dump_option('time', tf)
        
        if not 'time' in self._dump_options():
            self._set_dump_option('time', make_filter('all'))
            
        if not stats_week and not stats_month:
            for kind in ['day', 'week', 'month']:
                self._set_dump_option(kind, True)
        else:
            self._set_dump_option('day', stats_day)
            self._set_dump_option('week', stats_week)
            self._set_dump_option('month', stats_month)
            
        self._filter = ", ".join(self._filter.split(','))
        
    def process(self):
        self._process_filter()
        
        for j in self._jobs:
            if j == 'check-days':
                output('Day check (' + self._filter + '):')
                Statistics(self._universe).check_days(self._get_dump_option('time'))
            elif j == 'work-packages':
                output('Work package summary (' + self._filter + '):')
                act = self._universe.workpackage_root.calc_activity(self._get_dump_option('time'))
                act.dump(self._dump_options())
            elif j == 'tally-days':
                output('Time at work overview (' + self._filter + '):')
                Statistics(self._universe).calc_balance(self._dump_options())
            elif j == 'show-work-packages':
                output('Work package breakdown:')
                self._universe.workpackage_root.dump(self._dump_options())
            elif j == 'bill-of-materials':
                output('Bill of materials:')
                self._universe.bill_of_materials()
            else:
                output('*** Unknown job: ' + j)

    def show_usage(self, cmd):
        output()
        output('  Usage: ' + cmd + ' [options] <infile> [..]')
        output('''
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
      --version : show TimeFlies' version info
      --copyright : show copyright info
      -b, --bill-of-materials : list all input files processed; can be used
          to get an overview of all imported files
      -f, --filter <filter> : a filter to select a processing time range;
          YYYY-MM selects a month; YYYY-MM-DD..YYYY-MM-DD selects a time range
          by giving the first and last day; 'all' to process all days;
          for option -t summary cycles of 'day', 'week' and 'month' (or
          combinations thereof) can be added with the filter option too;
          to combine multiple items, use a comma separated list;
          default: process all
      -t, --tally-days : calculate the total must/have/leave/sick
          work hour balance
      -c, --check-days : check the daily work time vs. booked
          work package time; helps to find unaccounted for time at work
      -w, --work-packages : calculate hours worked on work packages
      -s, --show-work-packages : show the work package tree
      -a, --activities : show activities in work package tree output (in options
          -w, -s or -t)
      -C, --comments : show log comments for each day (in option -t)
      -i, --indent <width> : indent each level in the work package hierarchy by
          <width> space characters; default: 4

    Examples:
    
    timeflies.py -t -f 2012-07,week : calculate weekly work hour summaries for
    the month of July 2012.
    
    ... more to follow ...
    '''.format(_version))

def main(argv):
    app = Application()
    app.interpret_cmdline(argv)
    app.read_files()
    app.process()
    
if __name__ == '__main__':
    main(sys.argv)
