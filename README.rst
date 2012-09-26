=========
TimeFlies
=========

TimeFlies is a light weight acitvity logging and time tracking application with support for work package hierarchies. You keep your log data in one or more plain text files and TimeFlies will analyse them and generate the reports you want.

Installation
------------

Just download timeflies.py_ and stick anywhere convenient. It needs Python 3 and expects it in ``/usr/bin/python3``.

.. _timeflies.py: https://raw.github.com/42i/timeflies/master/src/timeflies.py

Manual
------

There also is a `TimeFlies PDF manual`_.

.. _`TimeFlies PDF manual`: https://github.com/downloads/42i/timeflies/timeflies.pdf

Examples
--------

Stick your work package structure and work log data in a text file ``time.fly``::

    work-package changer; does some heavy changing
        input
            xml
            json
        process
            step1
            step2
            step3
        output
            bin
            txt
    
    day 2012-07-12 8 17 # worked from 8 in the morning till 5 in the afternoon
    - changer.input.xml 2; simple nodes and vertices
    - changer.process.step1 3; simple node list handling
    - changer.output.txt 4; just nodes
    day 2012-07-13 8 11:30
    - changer.input.json 3; nodes and dicts
    - changer.input.xml 0.5; added comment parsing
    
    leave-days 2012-07-14 2012-08-05 # yayy, off to the seaside
    
    day 2012-08-06 10:00 15:15
    - changer.process.step2 2.5; vertex maps implemented 
    - changer.process.step1 2.75; adapted dicts to use vertex maps
    day 2012-08-07 9:00 20:00
    - changer.process.step3 6; simple linear filtering
    - changer.output.bin 5; single node binary serialisation

Now let TimeFlies loose on this.

The effort spent on each work package::

	$ timeflies.py -w time.fly 
    Work package summary (all):
      28.75 : ALL
          28.75 : changer; does some heavy changing
               5.50 : input
                   2.50 : xml
                   3.00 : json
              14.25 : process
                   5.75 : step1
                   2.50 : step2
                   6.00 : step3
               9.00 : output
                   5.00 : bin
                   4.00 : txt

The same annotated with the daily comments::

    $ timeflies.py -w -a time.fly 
    Work package summary (all):
      28.75 : ALL
          28.75 : changer; does some heavy changing
               5.50 : input
                   2.50 : xml
                          - 2012-07-12 2.0; simple nodes and vertices
                          - 2012-07-13 0.5; added comment parsing
                   3.00 : json
                          - 2012-07-13 3.0; nodes and dicts
              14.25 : process
                   5.75 : step1
                          - 2012-07-12 3.0; simple node list handling
                          - 2012-08-06 2.75; adapted dicts to use vertex maps
                   2.50 : step2
                          - 2012-08-06 2.5; vertex maps implemented
                   6.00 : step3
                          - 2012-08-07 6.0; simple linear filtering
               9.00 : output
                   5.00 : bin
                          - 2012-08-07 5.0; single node binary serialisation
                   4.00 : txt
                          - 2012-07-12 4.0; just nodes
                          
Now without comments, by month::

    $ timeflies.py -w -f 2012-07 time.fly 
    Work package summary (2012-07):
      12.50 : ALL
          12.50 : changer; does some heavy changing
               5.50 : input
                   2.50 : xml
                   3.00 : json
               3.00 : process
                   3.00 : step1
               4.00 : output
                   4.00 : txt
    
    $ timeflies.py -w -f 2012-08 time.fly 
    Work package summary (2012-08):
      16.25 : ALL
          16.25 : changer; does some heavy changing
              11.25 : process
                   2.75 : step1
                   2.50 : step2
                   6.00 : step3
               5.00 : output
                   5.00 : bin

And you worked in total::

    $ timeflies.py -t time.fly 
    Time at work overview (all):
    2012-07-12, Thu:    9.00 worked, ----.-- leave, ----.-- sick
    2012-07-13, Fri:    3.50 worked, ----.-- leave, ----.-- sick
       week 2012-28:   12.50 worked, ----.-- leave, ----.-- sick
    2012-07-16, Mon: ----.-- worked,    8.00 leave, ----.-- sick
    2012-07-17, Tue: ----.-- worked,    8.00 leave, ----.-- sick
    2012-07-18, Wed: ----.-- worked,    8.00 leave, ----.-- sick
    2012-07-19, Thu: ----.-- worked,    8.00 leave, ----.-- sick
    2012-07-20, Fri: ----.-- worked,    8.00 leave, ----.-- sick
       week 2012-29: ----.-- worked,   40.00 leave, ----.-- sick
    2012-07-23, Mon: ----.-- worked,    8.00 leave, ----.-- sick
    2012-07-24, Tue: ----.-- worked,    8.00 leave, ----.-- sick
    2012-07-25, Wed: ----.-- worked,    8.00 leave, ----.-- sick
    2012-07-26, Thu: ----.-- worked,    8.00 leave, ----.-- sick
    2012-07-27, Fri: ----.-- worked,    8.00 leave, ----.-- sick
       week 2012-30: ----.-- worked,   40.00 leave, ----.-- sick
    2012-07-30, Mon: ----.-- worked,    8.00 leave, ----.-- sick
    2012-07-31, Tue: ----.-- worked,    8.00 leave, ----.-- sick
      month 2012-07:   12.50 worked,   96.00 leave, ----.-- sick
    2012-08-01, Wed: ----.-- worked,    8.00 leave, ----.-- sick
    2012-08-02, Thu: ----.-- worked,    8.00 leave, ----.-- sick
    2012-08-03, Fri: ----.-- worked,    8.00 leave, ----.-- sick
       week 2012-31: ----.-- worked,   40.00 leave, ----.-- sick
    2012-08-06, Mon:    5.25 worked, ----.-- leave, ----.-- sick
    2012-08-07, Tue:   11.00 worked, ----.-- leave, ----.-- sick
       week 2012-32:   16.25 worked, ----.-- leave, ----.-- sick
      month 2012-08:   16.25 worked,   24.00 leave, ----.-- sick
              total:   28.75 worked,  120.00 leave, ----.-- sick

The same filtered by month only::

    $ timeflies.py -t -f month time.fly 
    Time at work overview (month):
      month 2012-07:   12.50 worked,   96.00 leave, ----.-- sick
      month 2012-08:   16.25 worked,   24.00 leave, ----.-- sick
              total:   28.75 worked,  120.00 leave, ----.-- sick

Or filtered by week::

    $ timeflies.py -t -f week time.fly 
    Time at work overview (week):
       week 2012-28:   12.50 worked, ----.-- leave, ----.-- sick
       week 2012-29: ----.-- worked,   40.00 leave, ----.-- sick
       week 2012-30: ----.-- worked,   40.00 leave, ----.-- sick
       week 2012-31: ----.-- worked,   40.00 leave, ----.-- sick
       week 2012-32:   16.25 worked, ----.-- leave, ----.-- sick
              total:   28.75 worked,  120.00 leave, ----.-- sick


