=========
TimeFlies
=========

TimeFlies is a light weight activity logging and time tracking application with
support for work package hierarchies. You keep your log data in one or more plain
text files and TimeFlies will analyse them and generate the reports you want.

Installation
------------

From packaged ZIP files containing both timeflies.py and the PDF manual:

- TimeFlies-0.5-2012-11-10.zip_
- TimeFlies-0.4-2012-10-16.zip_
- TimeFlies-0.3-2012-09-27.zip_

.. _TimeFlies-0.5-2012-11-10.zip: https://github.com/downloads/42i/timeflies/TimeFlies-0.5-2012-11-10.zip
.. _TimeFlies-0.4-2012-10-16.zip: https://github.com/downloads/42i/timeflies/TimeFlies-0.4-2012-10-16.zip
.. _TimeFlies-0.3-2012-09-27.zip: https://github.com/downloads/42i/timeflies/TimeFlies-0.3-2012-09-27.zip

Straight out of the repository:

- timeflies.py_, timeflies.pdf_, change-log.txt_

.. _timeflies.py: https://raw.github.com/42i/timeflies/master/src/timeflies.py
.. _timeflies.pdf: https://raw.github.com/42i/timeflies/master/doc/timeflies.pdf
.. _change-log.txt: https://raw.github.com/42i/timeflies/master/doc/change-log.txt

Required: Python 3 in ``/usr/bin/python3``.

Examples
--------

Stick your work package structure and work log data in a text file, say, ``time.fly``::

    # The project you're working on is the changer here.
    
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
  
    # You have standard 8 hour work days.
    
    must-hours mon..fri=8
    
    # And here your work log.
    
    day 2012-07-12 8 17 # worked from 8 in the morning till 5 in the afternoon
    - changer.input.xml 2; simple nodes and vertices
    - changer.process.step1 3; simple node list handling
    - changer.output.txt 4; just nodes
    
    day 2012-07-13 8 11:30
    - changer.input.json 3; nodes and dicts
    - changer.input.xml 0.5; added comment parsing
    
    leave-days 2012-07-14 2012-08-05; off to the seaside
    
    day 2012-08-06 10:00 15:15
    - changer.process.step2 2.5; vertex maps implemented 
    - changer.process.step1 2.75; adapted dicts to use vertex maps
    
    day 2012-08-07 9:00 20:00
    - changer.process.step3 6; simple linear filtering
    - changer.output.bin 5; single node binary serialisation

Now let TimeFlies loose on this.

The effort spent on each work package::

    $ timeflies -w time.fly 
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

    $ timeflies -w -a time.fly 
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

    $ timeflies -w -f 2012-07 time.fly 
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
    
    $ timeflies -w -f 2012-08 time.fly 
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

    $ timeflies -t time.fly 
    Time at work overview (all):
         when        worked   leave    sick balance
    2012-07-12 Thu:    9.00 ----.-- ----.--    1.00
    2012-07-13 Fri:    3.50 ----.-- ----.--   -4.50
      week 2012-28:   12.50 ----.-- ----.--   -3.50
    2012-07-16 Mon: ----.--    8.00 ----.-- ----.-- off to the seaside
    2012-07-17 Tue: ----.--    8.00 ----.-- ----.-- off to the seaside
    2012-07-18 Wed: ----.--    8.00 ----.-- ----.-- off to the seaside
    2012-07-19 Thu: ----.--    8.00 ----.-- ----.-- off to the seaside
    2012-07-20 Fri: ----.--    8.00 ----.-- ----.-- off to the seaside
      week 2012-29: ----.--   40.00 ----.-- ----.--
    2012-07-23 Mon: ----.--    8.00 ----.-- ----.-- off to the seaside
    2012-07-24 Tue: ----.--    8.00 ----.-- ----.-- off to the seaside
    2012-07-25 Wed: ----.--    8.00 ----.-- ----.-- off to the seaside
    2012-07-26 Thu: ----.--    8.00 ----.-- ----.-- off to the seaside
    2012-07-27 Fri: ----.--    8.00 ----.-- ----.-- off to the seaside
      week 2012-30: ----.--   40.00 ----.-- ----.--
    2012-07-30 Mon: ----.--    8.00 ----.-- ----.-- off to the seaside
    2012-07-31 Tue: ----.--    8.00 ----.-- ----.-- off to the seaside
     month 2012-07:   12.50   96.00 ----.--   -3.50
    2012-08-01 Wed: ----.--    8.00 ----.-- ----.-- off to the seaside
    2012-08-02 Thu: ----.--    8.00 ----.-- ----.-- off to the seaside
    2012-08-03 Fri: ----.--    8.00 ----.-- ----.-- off to the seaside
      week 2012-31: ----.--   40.00 ----.-- ----.--
    2012-08-06 Mon:    5.25 ----.-- ----.--   -2.75
    2012-08-07 Tue:   11.00 ----.-- ----.--    3.00
      week 2012-32:   16.25 ----.-- ----.--    0.25
     month 2012-08:   16.25   24.00 ----.--    0.25
             total:   28.75  120.00 ----.--   -3.25
         when        worked   leave    sick balance

The same filtered by month only::

    $ timeflies -t -f month time.fly 
    Time at work overview (month):
         when        worked   leave    sick balance
     month 2012-07:   12.50   96.00 ----.--   -3.50
     month 2012-08:   16.25   24.00 ----.--    0.25
             total:   28.75  120.00 ----.--   -3.25
         when        worked   leave    sick balance

Or filtered by week::

    $ timeflies -t -f week time.fly 
    Time at work overview (week):
         when        worked   leave    sick balance
      week 2012-28:   12.50 ----.-- ----.--   -3.50
      week 2012-29: ----.--   40.00 ----.-- ----.--
      week 2012-30: ----.--   40.00 ----.-- ----.--
      week 2012-31: ----.--   40.00 ----.-- ----.--
      week 2012-32:   16.25 ----.-- ----.--    0.25
             total:   28.75  120.00 ----.--   -3.25
         when        worked   leave    sick balance


