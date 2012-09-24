
EXAMPLES = fly-1.in fly-2.in fly-3.in fly-4.in \
		   fly-5.in fly-5a.out fly-5b.out \
		   fly-6.in fly-6a.out fly-6b.out fly-6c.out \
		   fly-7.in fly-7a.out fly-7b.out \
		   fly-8.in \
		   fly-9.in fly-9a.out fly-9b.out fly-9c.out fly-9d.out

show : manual.pdf
	evince $<

manual.pdf : manual.tex $(EXAMPLES)
	xelatex $^ && xelatex $^

clean :
	rm -f $(EXAMPLES) *~ manual.log manual.aux manual.toc
	
%.in: %.plain
	echo '% generated from '$< > $@
	echo '\\begin{inputfile}' >> $@
	cat $< >> $@
	echo '\\end{inputfile}' >> $@

fly-5a.out : fly-5.plain
	echo '% generated from '$< > $@
	echo '\\begin{inputfile}' >> $@
	echo '> timeflies.py -t work-log.fly' >> $@
	../src/timeflies.py -t $^ >> $@
	echo '\\end{inputfile}' >> $@

fly-5b.out : fly-5.plain
	echo '% generated from '$< > $@
	echo '\\begin{inputfile}' >> $@
	echo '> timeflies.py -t -C work-log.fly' >> $@
	../src/timeflies.py -t -C $^ >> $@
	echo '\\end{inputfile}' >> $@

fly-6a.out : fly-6.plain
	echo '% generated from '$< > $@
	echo '\\begin{inputfile}' >> $@
	echo '> timeflies.py -w work-log.fly' >> $@
	../src/timeflies.py -w $^ >> $@
	echo '\\end{inputfile}' >> $@

fly-6b.out : fly-6.plain
	echo '% generated from '$< > $@
	echo '\\begin{inputfile}' >> $@
	echo '> timeflies.py -w -a work-log.fly' >> $@
	../src/timeflies.py -w -a $^ >> $@
	echo '\\end{inputfile}' >> $@

fly-6c.out : fly-6.plain
	echo '% generated from '$< > $@
	echo '\\begin{inputfile}' >> $@
	echo '> timeflies.py -c work-log.fly' >> $@
	../src/timeflies.py -c $^ >> $@
	echo '\\end{inputfile}' >> $@

fly-7a.out : fly-7.plain fly-8.plain
	echo '% generated from '$< > $@
	echo '\\begin{inputfile}' >> $@
	echo '> timeflies.py -w prj-mighty-digester.fly work-log.fly' >> $@
	../src/timeflies.py -w $^ >> $@
	echo '\\end{inputfile}' >> $@

fly-7b.out : fly-7.plain fly-8.plain
	echo '% generated from '$< > $@
	echo '\\begin{inputfile}' >> $@
	echo '> timeflies.py -w -a prj-mighty-digester.fly work-log.fly' >> $@
	../src/timeflies.py -w -a $^ >> $@
	echo '\\end{inputfile}' >> $@

fly-9a.out : fly-9.plain
	echo '% generated from '$< > $@
	echo '\\begin{inputfile}' >> $@
	echo '> timeflies.py -t -f week work-log.fly' >> $@
	../src/timeflies.py -t -f week $^ >> $@
	echo '\\end{inputfile}' >> $@

fly-9b.out : fly-9.plain
	echo '% generated from '$< > $@
	echo '\\begin{inputfile}' >> $@
	echo '> timeflies.py -t -f week,month work-log.fly' >> $@
	../src/timeflies.py -t -f week,month $^ >> $@
	echo '\\end{inputfile}' >> $@

fly-9c.out : fly-9.plain
	echo '% generated from '$< > $@
	echo '\\begin{inputfile}' >> $@
	echo '> timeflies.py -t -f 2012-09 work-log.fly' >> $@
	../src/timeflies.py -t -f 2012-09 $^ >> $@
	echo '\\end{inputfile}' >> $@

fly-9d.out : fly-9.plain
	echo '% generated from '$< > $@
	echo '\\begin{inputfile}' >> $@
	echo '> timeflies.py -t -f week,2012-09 work-log.fly' >> $@
	../src/timeflies.py -t -f week,2012-09 $^ >> $@
	echo '\\end{inputfile}' >> $@


