#!/usr/bin/env python

# pazookle rewrite of the chuck example from
#	chuck.cs.princeton.edu/doc/examples/basic/demo0.ck
# "basic demo showing time and duration"

from pazookle.shred import zook,now


def main():
	zook.spork(demo0())
	zook.run()


def demo0():
	later = now() + 5*zook.sec

	while (now() < later):
		print now()
		yield zook.sec

	print now()


if __name__ == "__main__": main()
