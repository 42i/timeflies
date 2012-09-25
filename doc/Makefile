
EXAMPLES = fly-1.in fly-2.in fly-3.in fly-4.in \
		   fly-5.in fly-5a.out fly-5b.out \
		   fly-6.in fly-6a.out fly-6b.out fly-6c.out \
		   fly-7.in fly-7-wp.in fly-7a.out fly-7b.out \
		   fly-8.in fly-8a.out fly-8b.out fly-8c.out fly-8d.out

show : timeflies.pdf
	evince $<

timeflies.pdf : timeflies.tex $(EXAMPLES)
	xelatex $^ && xelatex $^

clean :
	rm -f $(EXAMPLES) *~ timeflies.log timeflies.aux timeflies.toc
	
fly-%.in: ex-%/work-log.fly
	./wrap-input.py $< > $@

fly-7-wp.in : ex-7/prj-mighty-digester.fly
	./wrap-input.py $< > $@

fly-5a.out : ex-5/work-log.fly
	./generate-output.py -t $^ > $@

fly-5b.out : ex-5/work-log.fly
	./generate-output.py -t -C $^ > $@

fly-6a.out : ex-6/work-log.fly
	./generate-output.py -w $^ > $@

fly-6b.out : ex-6/work-log.fly
	./generate-output.py -w -a $^ > $@

fly-6c.out : ex-6/work-log.fly
	./generate-output.py -c $^ > $@

fly-7a.out : ex-7/prj-mighty-digester.fly ex-7/work-log.fly
	./generate-output.py -w $^ > $@

fly-7b.out : ex-7/prj-mighty-digester.fly ex-7/work-log.fly
	./generate-output.py -w -a $^ > $@

fly-8a.out : ex-8/work-log.fly
	./generate-output.py -t -f week $^ > $@

fly-8b.out : ex-8/work-log.fly
	./generate-output.py -t -f week,month $^ > $@

fly-8c.out : ex-8/work-log.fly
	./generate-output.py -t -f 2012-09 $^ > $@

fly-8d.out : ex-8/work-log.fly
	./generate-output.py -t -f week,2012-09 $^ > $@


