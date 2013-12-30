#!/usr/bin/env python
"""
	Pazookle Audio Programming Language
	Copyright (C) 2013 Bob Harris.  All rights reserved.

    This file is part of Pazookle.

	Pazookle is free software: you can redistribute it and/or modify it under
	the terms of the GNU General Public License as published by the Free
	Software Foundation, either version 3 of the License, or (at your option)
	any later version.

	This program is distributed in the hope that it will be useful, but WITHOUT
	ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
	FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
	more details.

	You should have received a copy of the GNU General Public License along
	with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
__version__   = "0.01"
__author__    = "Bob Harris (zackobelsch@gmail.com)"
__copyright__ = "(C) 2013 Bob Harris. GNU GPLv3."

from sys    import stdout,stderr
from wave   import open as wave_open
from struct import pack as struct_pack
from ugen   import UGen,PassThru
from util   import clip_value


class TextOut(PassThru):
	"""Write the input value(s) to a file (or stdout).

	The output is a tab-delimited table.  The first column is the sample
	number.  The second column (or second and third for stereo) is the sample
	value.

	The filename argument can be a file object or a filename.  In the latter
	case we copen the file for write.  Note that we never close the file.  If
	no file or filename is provided we write to stdout.

	Unlike WavOut, the output samples are NOT clipped.
	"""

	def __init__(self,filename=None,channels=1,name=None):
		super(TextOut,self).__init__(channels=channels,name=name)
		if ("constructors" in UGen.debug): print >>stderr, "TextOut.__init__(%s)" % name
		self.ignoreInputlessSink = True
		self.sampleNum = 0
		if   (filename == None):      self.file = stdout
		elif (type(filename) == str): self.file = open(filename,"w")
		else:                         self.file = filename

	def close(self):
		if (self.file != stdout):
			self.file.close()

	def tick(self,sample,sample2=None):
		self.sampleNum += 1
		if (sample2 == None):
			print >>self.file, "%s\t%s" % (self.sampleNum,sample)
			return sample
		else:
			print >>self.file, "%s\t%s\t%s" % (self.sampleNum,sample,sample)
			return (sample,sample2)


class WavOut(PassThru):
	"""Write the input value(s) to a .wav file.

	The output samples are clipped to the maximum value supported by the file.
	"""
	# $$$ add support for 24 bits
	# $$$ setup shreduler list of unclosed wavOut objects, so it can close them upon exit 

	def __init__(self,filename=None,sampleWidth=2,channels=1,name=None):
		super(WavOut,self).__init__(channels=channels,name=name)
		if ("constructors" in UGen.debug): print >>stderr, "WavOut.__init__(%s)" % name
		if (filename == None):
			msg = "can't write to an unnamed wav file (for %s)" % self
			raise UGenError(msg)
		if (sampleWidth not in [1,2]):
			msg = "sampleWidth=%s is not supported (for %s)" % (sampleWidth,self)
			raise UGenError(msg)

		self.ignoreInputlessSink = True

		self.sampleWidth = sampleWidth
		self.sampleScale = (1<<(8*sampleWidth-1)) - 1
		if ("resolution" in UGen.debug):
			print >>stderr, "%s sampleWidth=%s sampleScale=%s" \
			              % (self,self.sampleWidth,self.sampleScale)
		if (sampleWidth == 1): self.packFormat = "b"
		else:                  self.packFormat = "h"
		self.wavFile = wavFile = wave_open(filename, "wb")

		wavFile.setparams((self.outChannels,self.sampleWidth,UGen.samplingRate,1,
		                   "NONE","not compressed"))

		UGen.add_sink(self)

	def close(self):
		UGen.remove_sink(self)
		self.wavFile.close()

	def tick(self,sample,sample2=None):
		if (sample2 == None):
			s1 = int(self.sampleScale*sample)
			s1 = clip_value(s1,-self.sampleScale,self.sampleScale)
			self.wavFile.writeframes(struct_pack(self.packFormat,s1))
			return sample
		else:
			s1 = int(self.sampleScale*sample)
			s1 = clip_value(s1,-self.sampleScale,self.sampleScale)
			s2 = int(self.sampleScale*sample2)
			s2 = clip_value(s2,-self.sampleScale,self.sampleScale)
			self.wavFile.writeframes(struct_pack(self.packFormat,s1))
			self.wavFile.writeframes(struct_pack(self.packFormat,s2))
			return (sample,sample2)
