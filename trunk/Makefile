test:
	rm -f /tmp/main.pov /tmp/test.pov test.png
	python nailcast2.py dot.png
	povray +H1000 +W1000 +Otest.png /tmp/main.pov
	xli test.png &

lenna:
	rm -f /tmp/main.pov /tmp/test.pov test.png
	python nailcast2.py Lenna.png
	povray +H2000 +W2000 +Otest.png /tmp/main.pov
	xli test.png &


obama:
	rm -f /tmp/main.pov /tmp/test.pov test.png
	python nailcast2.py obama1.jpg
	povray +H2000 +W2000 +Otest.png /tmp/main.pov
	xli test.png &
