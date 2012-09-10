
from datetime import date
import sys
import re
import weakref

def makeDate(dstr):
    datecomps = dstr.split('-')
    return date(int(datecomps[0]), int(datecomps[1]), int(datecomps[2]))

def isWeekend(d):
    return d.isoweekday() == 6 or d.isoweekday() == 7

def formatTimeVal(val, what):
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
        
class Task:
    def __init__(self, name, desc=None, effort=0):
        self.name = name
        self.parent = None
        self.description = desc
        self.effort = int(effort)
        self.subs = []
        self.subsByName = {}
        self.activities = []
        
    def calcEffort(self):
        e = self.effort
        for s in self.subs:
            e += s.calcEffort()
        return e
    
    def calcActivity(self, dayfilter, store, path=None):
        totals = 0.0;
        for a in self.activities:
            if dayfilter.passes(a.day()):
                totals += a.duration
        fullpath = self.name if path == None else path + '.' + self.name

        if totals != 0.0 and len(self.subs) > 0:
            store[fullpath + '.--self--'] = totals
        
        for s in self.subs:
            totals += s.calcActivity(dayfilter, store, fullpath)
        
        if totals != 0.0:
            store[fullpath] = totals
        return totals
        
    def addTask(self, task):
        idx = len(self.subs)
        self.subs.append(task)
        self.subsByName[task.name] = idx
        task.parent = weakref.ref(self)
    
    def getSubByName(self, name):
        return self.subs[self.subsByName[name]]
    
    def getTask(self, pathstr, create=False):
        path = pathstr.split('.')
        t = self
        for c in path:
            if c in t.subsByName:
                t = t.getSubByName(c)
            else:
                if not create:
                    return None
                else:
                    newt = Task(c)
                    t.addTask(newt)
                    t = newt
        return t
    
    def addActivity(self, activity):
        self.activities.append(activity)
        activity.task = weakref.ref(self)

    def dump(self, indent=''):
        if self.description != None:
            desc = ' -- ' + self.description
        else:
            desc = ''
        
        print(indent + self.name + desc)
        
        for a in self.activities:
            comment = (', ' + a.description) if a.description != None else ''
            print(indent + '    # ' + str(a.day().date) + ' ' + str(a.duration) + comment)
        
        if self.subs != None:
            for s in self.subs:
                s.dump(indent + '    ')

class Activity:
    def __init__(self, duration, description):
        self.day = None
        self.task = None
        self.duration = float(duration)
        self.description = description
        
class Day:
    """A Day object represents a day of work. It has a date,
    hour information and comment information attached to it."""
    def __init__(self, dstr):
        self.date = makeDate(dstr)
        self.directives = None
        self.start = 0
        self.stop = 0
        self.off = 0
        self.ill = 0
        self.leave = 0
        self.phol = False
        self.comments = []
        self.activities = []
        
    def addDirective(self, d):
        if self.directives == None:
            self.directives = [ d ]
        else:
            self.directives.append(d)
    
    def addActivity(self, activity):
        self.activities.append(activity)
        activity.day = weakref.ref(self)
        
    def addComment(self, comment):
        self.comments.append(comment)

    def addOff(self, off):
        self.off += off

    def setPhol(self, phol):
        self.phol = phol

    def addLeave(self, leave):
        self.leave += leave

    def addIll(self, ill):
        self.ill = ill

    def setHours(self, start, stop):
        self.start = start
        self.stop = stop

    def calcActivity(self):
        totals = 0.0
        for a in self.activities:
            totals += a.duration
        return totals
        
    def calcBalance(self):
        return self.calcWorked() + self.ill + self.leave

    def calcWorked(self):
        return self.stop - self.start - self.off
    
    def calcRequired(self):
        if self.phol or isWeekend(self.date):
            return 0.0
        else:
            return 8.0
    
    def dump(self):
        print(self.date.strftime('%Y-%m-%d, %a: ') + \
              formatTimeVal(self.calcWorked(), "worked") + ', ' +\
              formatTimeVal(self.leave, "leave") + ', ' +\
              formatTimeVal(self.ill, "ill"))

        
class Directive:
    def __init__(self):
        self.reset = False
        self.leave = None
        self.must = None
        self.have = None

    def setLeave(self, leave):
        self.leave = leave
        return self
    
    def setMust(self, must):
        self.must = must
        return self
    
    def setHave(self, have):
        self.have = have
        return self
    
    def setReset(self):
        self.reset = True
        return self

class Universe:
    def __init__(self):
        self.days = {}
        self.taskroot = Task("root", "the task of life")
        
    def getChronoDays(self):
        return sorted(self.days.values(), key = lambda day: day.date)
    
class TaskLineBookmark:
    def __init__(self, task, indent, parent=None):
        self.indent = indent
        self.task = task
        self.parent = parent

class Reader:
    def __init__(self, uni):
        self.universe = uni
        
    def read(self, inputfile):
        f = open(inputfile)
        self.linecount = 0
        self.currentday = None
        self.resetTaskStack()
        
        for line in f:
            self.linecount += 1
            line = re.sub(" *#.*", "", line).rstrip()
            
            if line == '':
                self.resetTaskStack()
            elif self.inTaskDefinition():
                self.processTask(line)
            elif line.startswith('task '):
                self.processTask(line[5:].strip())
            else:
                self.resetTaskStack()
                    
                if line.startswith('- '):
                    self.processActivity(line[2:].strip())
                elif line.startswith('-- '):
                    self.processComment(line[3:].strip())
                elif line.startswith('todo '):
                    if not self.currentday == None:
                        self.msg('WARNING: TO DO item found beyond the beginning of the file')
                    else:
                        self.msg('TO DO: ' + line[5:].strip())
                elif line.strip() != '':
                    self.processInstructions(line)
        f.close()
        
    def msg(self, text):
        print('Line ' + str(self.linecount) + ': ' + text)
        
    def resetTaskStack(self):
        self.taskstack = TaskLineBookmark(self.universe.taskroot, -1)

    def inTaskDefinition(self):
        return self.universe.taskroot != self.taskstack.task
    
    #   name.of.the.task [params ...], description
    def processTask(self, line):
        items = line.split(',', 1)
        spec = items[0].strip().split(' ')
        fullname = spec[0]
                
        indent = len(line) - len(line.lstrip())
        
        while indent <= self.taskstack.indent:
            self.taskstack = self.taskstack.parent
        
        task = self.taskstack.task.getTask(fullname, create=True)
        
        if len(spec) > 1: # effort
            task.effort = spec[1]
            
        if len(items) == 2: # description
            task.description = items[1].strip()
        
        self.taskstack = TaskLineBookmark(task, indent, self.taskstack)
        
    def processActivity(self, line):
        comps = line.split(',', 1)
        args = comps[0].strip().split(' ')
        if len(args) < 2:
            self.msg('an activity must have a task and a duration.')
        else:
            taskname = args[0]
            duration = args[1]
            if len(comps) == 2:
                desc = comps[1].strip()
            else:
                desc = None

            try:
                activity = Activity(duration, desc)
                task = self.universe.taskroot.getTask(taskname)
                if task == None:
                    self.msg('invalid activity task ' + taskname
                             + ' on day ' + str(self.currentday.date))
                else:
                    task.addActivity(activity)
                    self.currentday.addActivity(activity)
            except ValueError:
                self.msg('invalid activity duration ' + duration + '.')
            
        
    def processComment(self, comment):
        self.currentday.addComment(comment)

    def processInstructions(self, line):
        morsels = line.split(',')
        for mors in morsels:
            self.processInstruction(mors.strip())

    def addLeave(self, start, end, where):
        st = makeDate(start)
        end = makeDate(end)

        d = st.toordinal()
        end = end.toordinal()

        while d <= end:
            dt = date.fromordinal(d)

            if not isWeekend(dt):
                self.newDay(str(dt))
                self.currentday.addLeave(8.0)
                self.currentday.addComment('leave: ' + where)

            d = d + 1

    def newDay(self, datestring):
        if datestring in self.universe.days:
            self.currentday = self.universe.days[datestring]
        else:
            self.currentday = Day(datestring)
            self.universe.days[datestring] = self.currentday

    def processInstruction(self, argliststring):
        arglist = argliststring.split(' ')
        instr = arglist[0]
        args = arglist[1:]

        if instr == 'day':
            self.newDay(args[0])
            return
        
        if instr == 'leave' and len(args) == 3:
            self.addLeave(args[0], args[1], args[2])
            return
        
        if self.currentday == None:
            self.msg('No current day for instruction <' + argliststring + '>.')
            return
        
        if instr == 'reset':
            self.currentday.addDirective(Directive().setReset())
        elif instr == 'add-leave':
            self.currentday.addDirective(Directive().setLeave(float(args[0])))
        elif instr == 'balance-must':
            self.currentday.addDirective(Directive().setMust(float(args[0])))
        elif instr == 'balance-have':
            self.currentday.addDirective(Directive().setHave(float(args[0])))
        elif instr == 'off':
            self.currentday.addOff(float(args[0]))
        elif instr == 'hours':
            self.currentday.setHours(float(args[0]), float(args[1]))
        elif instr == 'leave':
            if len(args) == 2:
                self.currentday.addLeave(float(args[0]))
                self.currentday.addComment('leave: ' + args[1])
            else:
                self.msg('Weird leave spec <' + argliststring + '>.')
        else:
            self.msg('Weird instruction <' + argliststring + '>.')

class Status:
    def __init__(self, name):
        self.name = name
        self.reset()

    def reset(self):
        self.musthours = 0
        self.havehours = 0
        self.leavebalancehours = 0
        self.leavetakenhours = 0
        self.illhours = 0
        self.workedhours = 0

    def increaseMustHours(self, dt):
        # public holidays?
        workday = not isWeekend(dt)
        if workday:
            self.musthours += 8
        return workday
    
    def processDay(self, day):
        if day.directives != None:
            for di in day.directives:
                self.processDirective(di)

        self.musthours += day.calcRequired()
        self.havehours += day.calcBalance()
        self.workedhours += day.calcWorked()
        self.illhours += day.ill
        self.leavebalancehours -= day.leave
        self.leavetakenhours += day.leave
        
    def processDirective(self, di):
        if di.reset:
            self.dump()
            self.reset()
            #print('--- reset ' + self.name + '---')
        elif di.leave != None:
            self.leavebalancehours += di.leave
        elif di.must != None:
            self.musthours = di.must
        elif di.have != None:
            self.havehours = di.have
        
    def dump(self):
        print(self.name + ': must = {0:6.2f}, worked = {1:6.2f}, ill = {2:6.2f}, leave taken= {3:6.2f}, leave left = {4:6.2f}, have = {5:6.2f}'\
              .format(self.musthours, self.workedhours, self.illhours, self.leavetakenhours, self.leavebalancehours, self.havehours))

class Statistics:
    def __init__(self, universe):
        self.days = universe.getChronoDays()
        self.globalbalance = Status('global')
        self.weeklybalance = Status('weekly')
        self.previous = None

    def processGap(self, d1):
        if self.previous == None:
            return

        d = self.previous.date.toordinal() + 1
        end = d1.date.toordinal()

        while d < end:
            dt = date.fromordinal(d)
            if self.globalbalance.increaseMustHours(dt):
                print('missing weekday record for ' + str(dt))
            d = d + 1

    def checkDays(self, dayfilter):
        for d in self.days:
            if dayfilter.passes(d):
                delta = d.calcActivity() - d.calcWorked()
                if delta != 0.0:
                    print('*** {0:s} : delta = {1:5.2f}'.format(d.date.strftime('%Y-%m-%d, %a'), delta))
        
    def simple(self):
        self.previous = None
        for d in self.days:
            self.processGap(d)
            if d.date.isoweekday() == 1:
                self.weeklybalance.dump()
                print()
                self.weeklybalance.reset()
                
            self.weeklybalance.processDay(d)
            self.globalbalance.processDay(d)
            d.dump()
            self.previous = d

        self.weeklybalance.dump()
        self.globalbalance.dump()
              
# ===== ===== ===== Main ===== ===== =====

if __name__ == '__main__':
    sheetname = 'test/simple-project-2.fly' #sys.argv[1]
    sheetname = 'H:\Timesheet\work-book-2012-09.log' #sys.argv[1]
    u = Universe()
    r = Reader(u)
    r.read(sheetname)
    s = Statistics(u)
    month = MonthFilter(2012, 9)
    print('------------------')
    s.checkDays(month);
    print('------------------')
    u.taskroot.dump()
    act = {}
    u.taskroot.calcActivity(month, act)
    for tn in sorted(act.keys()):
        indentname = re.sub('[a-z0-9A-Z]+\.', '. . ', tn)
        print('{0:6.2f} {1:s}'.format(act[tn], indentname))





