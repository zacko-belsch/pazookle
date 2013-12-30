#!/usr/bin/env python
# see http://docs.python.org/2/library/unittest.html
# or  http://docs.python.org/2/library/test.html

import unittest
from StringIO          import StringIO
from pazookle.ugen     import UGen,Mixer,Pan
from pazookle.generate import Periodic

class TestUGen(unittest.TestCase):

	def setUp(self):
		UGen.set_debug("stifle ids")


	def test_inline_connect(self):
		# 	a >> b >> c              a is input to b
		# 	                         b is input to c
		expected = \
"""
a
b in[a]
c in[b]
"""
		a = UGen(name="a")
		b = UGen(name="b")
		c = UGen(name="c")

		a >> b >> c

		self.assertEqual(self.transcript([a,b,c]),expected)


	def test_list_connect(self):
		# 	a >> [b,c]               a is input to b
		# 	                         a is input to c
		expected = \
"""
a
b in[a]
c in[a]
"""
		a = UGen(name="a")
		b = UGen(name="b")
		c = UGen(name="c")

		a >> [b,c]

		self.assertEqual(self.transcript([a,b,c]),expected)


	def test_disallowed_list_connect(self):
		self.assertRaises(TypeError,self._test_disallowed_list_connect)

	def _test_disallowed_list_connect(self):
		# 	a >> [b,c] >> d          not allowed
		# 	                         (only allowed at right end of chain)
		a = UGen(name="a")
		b = UGen(name="b")
		c = UGen(name="c")
		d = UGen(name="d")

		a >> [b,c] >> d


	def test_added_connect(self):
		# 	b += a                   a is input to b
		expected = \
"""
a
b in[a]
"""
		a = UGen(name="a")
		b = UGen(name="b")

		b += a

		self.assertEqual(self.transcript([a,b]),expected)


	def test_added_list_connect(self):
		# 	a += [b,c]               b is input to a
		# 	                         c is input to a
		expected = \
"""
a in[b,c]
b
c
"""
		a = UGen(name="a")
		b = UGen(name="b")
		c = UGen(name="c")

		a += [b,c]

		self.assertEqual(self.transcript([a,b,c]),expected)


	def test_inline_bias_connect(self):
		# 	a + b >> c               a is input to b.bias
		# 	                         b (not b.bias) is input to c
		expected = \
"""
a
b bias[b~bias]
b~bias in[a] drives[b.bias]
c in[b]
"""
		a = UGen(name="a")
		b = UGen(name="b")
		c = UGen(name="c")

		a + b >> c

		self.assertEqual(self.transcript([a,b,b._bias,c]),expected)


	def test_lookup_bias_connect(self):
		# 	a >> b["bias"] >> c     a is input to b.bias
		# 	                         b (not b.bias) is input to c
		expected = \
"""
a
b bias[b~bias]
b~bias in[a] drives[b.bias]
c in[b]
"""
		a = UGen(name="a")
		b = UGen(name="b")
		c = UGen(name="c")

		a >> b["bias"] >> c

		self.assertEqual(self.transcript([a,b,b._bias,c]),expected)


	def test_assigned_bias_connect(self):
		# 	b.bias = a              a is input to b.bias
		expected = \
"""
a
b bias[b~bias]
b~bias in[a] drives[b.bias]
"""
		a = UGen(name="a")
		b = UGen(name="b")

		b.bias = a

		self.assertEqual(self.transcript([a,b,b._bias]),expected)


	def test_assigned_bias_lookup_connect(self):
		# 	b["bias"] = a           a is input to b.bias
		expected = \
"""
a
b bias[b~bias]
b~bias in[a] drives[b.bias]
"""
		a = UGen(name="a")
		b = UGen(name="b")

		b["bias"] = a

		self.assertEqual(self.transcript([a,b,b._bias]),expected)


#	def test_bias_7c(self):
#		# 	b.bias += a             a is input to b.bias
#		expected = \
#"""
#a
#b bias[b~bias]
#b~bias in[a] drives[b.bias]
#"""
#		a = UGen(name="a")
#		b = UGen(name="b")
#
#		b.bias += a
#
#		self.assertEqual(self.transcript([a,b,b._bias]),expected)


#	def test_bias_7d(self):
#		# 	b["bias"] += a          a is input to b.bias
#		expected = \
#"""
#a
#b bias[b~bias]
#b~bias in[a] drives[b.bias]
#"""
#		a = UGen(name="a")
#		b = UGen(name="b")
#
#		b["bias"] += a
#
#		self.assertEqual(self.transcript([a,b,b._bias]),expected)


	def test_inline_gain_connect(self):
		# 	a * b >> c               a is input to b.gain
		# 	                         b (not b.gain) is input to c
		expected = \
"""
a
b gain[b~gain]
b~gain in[a] drives[b.gain]
c in[b]
"""
		a = UGen(name="a")
		b = UGen(name="b")
		c = UGen(name="c")

		a * b >> c

		self.assertEqual(self.transcript([a,b,b._gain,c]),expected)


	def test_lookup_gain_connect(self):
		# 	a >> b["gain"] >> c     a is input to b.gain
		# 	                         b (not b.gain) is input to c
		expected = \
"""
a
b gain[b~gain]
b~gain in[a] drives[b.gain]
c in[b]
"""
		a = UGen(name="a")
		b = UGen(name="b")
		c = UGen(name="c")

		a >> b["gain"] >> c

		self.assertEqual(self.transcript([a,b,b._gain,c]),expected)


	def test_assigned_gain_connect(self):
		# 	b.gain = a              a is input to b.gain
		expected = \
"""
a
b gain[b~gain]
b~gain in[a] drives[b.gain]
"""
		a = UGen(name="a")
		b = UGen(name="b")

		b.gain = a

		self.assertEqual(self.transcript([a,b,b._gain]),expected)


	def test_assigned_gain_lookup_connect(self):
		# 	b["gain"] = a           a is input to b.gain
		expected = \
"""
a
b gain[b~gain]
b~gain in[a] drives[b.gain]
"""
		a = UGen(name="a")
		b = UGen(name="b")

		b["gain"] = a

		self.assertEqual(self.transcript([a,b,b._gain]),expected)


#	def test_gain_7c(self):
#		# 	b.gain += a             a is input to b.gain
#		expected = \
#"""
#a
#b gain[b~gain]
#b~gain in[a] drives[b.gain]
#"""
#		a = UGen(name="a")
#		b = UGen(name="b")
#
#		b.gain += a
#
#		self.assertEqual(self.transcript([a,b,b._gain]),expected)


#	def test_gain_7d(self):
#		# 	b["gain"] += a          a is input to b.gain
#		expected = \
#"""
#a
#b gain[b~gain]
#b~gain in[a] drives[b.gain]
#"""
#		a = UGen(name="a")
#		b = UGen(name="b")
#
#		b["gain"] += a
#
#		self.assertEqual(self.transcript([a,b,b._gain]),expected)


	def test_lookup_dry_connect(self):
		# 	a >> b["dry"] >> c     a is input to b.dry
		# 	                         b (not b.dry) is input to c
		expected = \
"""
a
b dry[b~dry]
b~dry in[a] drives[b.dry]
c in[b]
"""
		a = UGen(name="a")
		b = Mixer(name="b")
		c = UGen(name="c")

		a >> b["dry"] >> c

		self.assertEqual(self.transcript([a,b,b._dry,c]),expected)


	def test_assigned_dry_connect(self):
		# 	b.dry = a              a is input to b.dry
		expected = \
"""
a
b dry[b~dry]
b~dry in[a] drives[b.dry]
"""
		a = UGen(name="a")
		b = Mixer(name="b")

		b.dry = a

		self.assertEqual(self.transcript([a,b,b._dry]),expected)


	def test_assigned_dry_lookup_connect(self):
		# 	b["dry"] = a           a is input to b.dry
		expected = \
"""
a
b dry[b~dry]
b~dry in[a] drives[b.dry]
"""
		a = UGen(name="a")
		b = Mixer(name="b")

		b["dry"] = a

		self.assertEqual(self.transcript([a,b,b._dry]),expected)


#	def test_dry_7c(self):
#		# 	b.dry += a             a is input to b.dry
#		expected = \
#"""
#a
#b dry[b~dry]
#b~dry in[a] drives[b.dry]
#"""
#		a = UGen(name="a")
#		b = Mixer(name="b")
#
#		b.dry += a
#
#		self.assertEqual(self.transcript([a,b,b._dry]),expected)


#	def test_dry_7d(self):
#		# 	b["dry"] += a          a is input to b.dry
#		expected = \
#"""
#a
#b dry[b~dry]
#b~dry in[a] drives[b.dry]
#"""
#		a = UGen(name="a")
#		b = Mixer(name="b")
#
#		b["dry"] += a
#
#		self.assertEqual(self.transcript([a,b,b._dry]),expected)


	def test_lookup_wet_connect(self):
		# 	a >> b["wet"] >> c     a is input to b.wet
		# 	                         b (not b.wet) is input to c
		expected = \
"""
a
b wet[b~wet]
b~wet in[a] drives[b.wet]
c in[b]
"""
		a = UGen(name="a")
		b = Mixer(name="b")
		c = UGen(name="c")

		a >> b["wet"] >> c

		self.assertEqual(self.transcript([a,b,b._wet,c]),expected)


	def test_assigned_wet_connect(self):
		# 	b.wet = a              a is input to b.wet
		expected = \
"""
a
b wet[b~wet]
b~wet in[a] drives[b.wet]
"""
		a = UGen(name="a")
		b = Mixer(name="b")

		b.wet = a

		self.assertEqual(self.transcript([a,b,b._wet]),expected)


	def test_assigned_wet_lookup_connect(self):
		# 	b["wet"] = a           a is input to b.wet
		expected = \
"""
a
b wet[b~wet]
b~wet in[a] drives[b.wet]
"""
		a = UGen(name="a")
		b = Mixer(name="b")

		b["wet"] = a

		self.assertEqual(self.transcript([a,b,b._wet]),expected)


#	def test_wet_7c(self):
#		# 	b.wet += a             a is input to b.wet
#		expected = \
#"""
#a
#b wet[b~wet]
#b~wet in[a] drives[b.wet]
#"""
#		a = UGen(name="a")
#		b = Mixer(name="b")
#
#		b.wet += a
#
#		self.assertEqual(self.transcript([a,b,b._wet]),expected)


#	def test_wet_7d(self):
#		# 	b["wet"] += a          a is input to b.wet
#		expected = \
#"""
#a
#b wet[b~wet]
#b~wet in[a] drives[b.wet]
#"""
#		a = UGen(name="a")
#		b = Mixer(name="b")
#
#		b["wet"] += a
#
#		self.assertEqual(self.transcript([a,b,b._wet]),expected)


	def test_lookup_pan_connect(self):
		# 	a >> b["pan"] >> c     a is input to b.pan
		# 	                         b (not b.pan) is input to c
		expected = \
"""
a
b pan[b~pan]
b~pan in[a] drives[b.pan]
c in[b]
"""
		a = UGen(name="a")
		b = Pan(name="b")
		c = UGen(name="c")

		a >> b["pan"] >> c

		self.assertEqual(self.transcript([a,b,b._pan,c]),expected)


	def test_assigned_pan_connect(self):
		# 	b.pan = a              a is input to b.pan
		expected = \
"""
a
b pan[b~pan]
b~pan in[a] drives[b.pan]
"""
		a = UGen(name="a")
		b = Pan(name="b")

		b.pan = a

		self.assertEqual(self.transcript([a,b,b._pan]),expected)


	def test_assigned_pan_lookup_connect(self):
		# 	b["pan"] = a           a is input to b.pan
		expected = \
"""
a
b pan[b~pan]
b~pan in[a] drives[b.pan]
"""
		a = UGen(name="a")
		b = Pan(name="b")

		b["pan"] = a

		self.assertEqual(self.transcript([a,b,b._pan]),expected)


#	def test_pan_7c(self):
#		# 	b.pan += a             a is input to b.pan
#		expected = \
#"""
#a
#b pan[b~pan]
#b~pan in[a] drives[b.pan]
#"""
#		a = UGen(name="a")
#		b = Pan(name="b")
#
#		b.pan += a
#
#		self.assertEqual(self.transcript([a,b,b._pan]),expected)


#	def test_pan_7d(self):
#		# 	b["pan"] += a          a is input to b.pan
#		expected = \
#"""
#a
#b pan[b~pan]
#b~pan in[a] drives[b.pan]
#"""
#		a = UGen(name="a")
#		b = Pan(name="b")
#
#		b["pan"] += a
#
#		self.assertEqual(self.transcript([a,b,b._pan]),expected)


	def test_inline_freq_connect(self):
		# 	a % b >> c               a is input to b.freq
		# 	                         b (not b.freq) is input to c
		expected = \
"""
a
b freq[b~freq]
b~freq in[a] drives[b.freq]
c in[b]
"""
		a = UGen(name="a")
		b = Periodic(name="b")
		c = UGen(name="c")

		a % b >> c

		self.assertEqual(self.transcript([a,b,b._freq,c]),expected)


	def test_lookup_freq_connect(self):
		# 	a >> b["freq"] >> c     a is input to b.freq
		# 	                         b (not b.freq) is input to c
		expected = \
"""
a
b freq[b~freq]
b~freq in[a] drives[b.freq]
c in[b]
"""
		a = UGen(name="a")
		b = Periodic(name="b")
		c = UGen(name="c")

		a >> b["freq"] >> c

		self.assertEqual(self.transcript([a,b,b._freq,c]),expected)


	def test_assigned_freq_connect(self):
		# 	b.freq = a              a is input to b.freq
		expected = \
"""
a
b freq[b~freq]
b~freq in[a] drives[b.freq]
"""
		a = UGen(name="a")
		b = Periodic(name="b")

		b.freq = a

		self.assertEqual(self.transcript([a,b,b._freq]),expected)


	def test_assigned_freq_lookup_connect(self):
		# 	b["freq"] = a           a is input to b.freq
		expected = \
"""
a
b freq[b~freq]
b~freq in[a] drives[b.freq]
"""
		a = UGen(name="a")
		b = Periodic(name="b")

		b["freq"] = a

		self.assertEqual(self.transcript([a,b,b._freq]),expected)


#	def test_freq_7c(self):
#		# 	b.freq += a             a is input to b.freq
#		expected = \
#"""
#a
#b freq[b~freq]
#b~freq in[a] drives[b.freq]
#"""
#		a = UGen(name="a")
#		b = Periodic(name="b")
#
#		b.freq += a
#
#		self.assertEqual(self.transcript([a,b,b._freq]),expected)


#	def test_freq_7d(self):
#		# 	b["freq"] += a          a is input to b.freq
#		expected = \
#"""
#a
#b freq[b~freq]
#b~freq in[a] drives[b.freq]
#"""
#		a = UGen(name="a")
#		b = Periodic(name="b")
#
#		b["freq"] += a
#
#		self.assertEqual(self.transcript([a,b,b._freq]),expected)


	def test_lookup_phase_connect(self):
		# 	a >> b["phase"] >> c     a is input to b.phase
		# 	                         b (not b.phase) is input to c
		expected = \
"""
a
b phase[b~phase]
b~phase in[a] drives[b.phase]
c in[b]
"""
		a = UGen(name="a")
		b = Periodic(name="b")
		c = UGen(name="c")

		a >> b["phase"] >> c

		self.assertEqual(self.transcript([a,b,b._phase,c]),expected)


	def test_assigned_phase_connect(self):
		# 	b.phase = a              a is input to b.phase
		expected = \
"""
a
b phase[b~phase]
b~phase in[a] drives[b.phase]
"""
		a = UGen(name="a")
		b = Periodic(name="b")

		b.phase = a

		self.assertEqual(self.transcript([a,b,b._phase]),expected)


	def test_assigned_phase_lookup_connect(self):
		# 	b["phase"] = a           a is input to b.phase
		expected = \
"""
a
b phase[b~phase]
b~phase in[a] drives[b.phase]
"""
		a = UGen(name="a")
		b = Periodic(name="b")

		b["phase"] = a

		self.assertEqual(self.transcript([a,b,b._phase]),expected)


#	def test_phase_7c(self):
#		# 	b.phase += a             a is input to b.phase
#		expected = \
#"""
#a
#b phase[b~phase]
#b~phase in[a] drives[b.phase]
#"""
#		a = UGen(name="a")
#		b = Periodic(name="b")
#
#		b.phase += a
#
#		self.assertEqual(self.transcript([a,b,b._phase]),expected)


#	def test_phase_7d(self):
#		# 	b["phase"] += a          a is input to b.phase
#		expected = \
#"""
#a
#b phase[b~phase]
#b~phase in[a] drives[b.phase]
#"""
#		a = UGen(name="a")
#		b = Periodic(name="b")
#
#		b["phase"] += a
#
#		self.assertEqual(self.transcript([a,b,b._phase]),expected)


	def test_disconnect(self):
		# 	a >> b >> c
		#	a // b
		expected = \
"""
a
b
c in[b]
"""
		a = UGen(name="a")
		b = UGen(name="b")
		c = UGen(name="c")

		a >> b >> c
		a // b

		self.assertEqual(self.transcript([a,b,c]),expected)


	def test_inline_disconnect(self):
		# 	a >> b >> c
		#	a // b // c
		expected = \
"""
a
b
c
"""
		a = UGen(name="a")
		b = UGen(name="b")
		c = UGen(name="c")

		a >> b >> c
		a // b // c

		self.assertEqual(self.transcript([a,b,c]),expected)


	def test_all_inputs_disconnect(self):
		# 	a >> b["bias"] >> c
		#   a >> b
		#	a // b
		expected = \
"""
a
b
c in[b]
"""
		a = UGen(name="a")
		b = UGen(name="b")
		c = UGen(name="c")

		a >> b["bias"] >> c
		a >> b
		a // b

		self.assertEqual(self.transcript([a,b,c]),expected)


	def test_bias_disconnect(self):
		# 	a >> b["bias"] >> c
		#   a >> b
		#	a // b["bias"]
		expected = \
"""
a
b in[a]
c in[b]
"""
		a = UGen(name="a")
		b = UGen(name="b")
		c = UGen(name="c")

		a >> b["bias"] >> c
		a >> b
		a // b["bias"]

		self.assertEqual(self.transcript([a,b,c]),expected)

	def test_LR_connect_to(self):
		# 	a >> c["left"]
		#   b >> c["right"]
		expected = \
"""
a
b
c in[(a,>L),(b,>R)]
"""
		a = UGen(name="a")
		b = UGen(name="b")
		c = UGen(name="c")

		a >> c["left"]
		b >> c["right"]

		self.assertEqual(self.transcript([a,b,c]),expected)


	def test_lookup_LR_connect(self):
		# 	a >> c["left"]  >> d     a is input to c.left;  c.left is input to d
		# 	b >> c["right"] >> e     b is input to c.right; c.right is input to e
		# 	                         
		expected = \
"""
a
b
c in[(a,>L),(b,>R)]
d in[(c,L>)]
e in[(c,R>)]
"""
		a = UGen(name="a")
		b = UGen(name="b")
		c = UGen(name="c")
		d = UGen(name="d")
		e = UGen(name="e")

		a >> c["left"]  >> d
		b >> c["right"] >> e

		self.assertEqual(self.transcript([a,b,c,d,e]),expected)


	def test_assigned_LR_connect(self):
		# 	c.left  = a
		# 	c.right = b
		expected = \
"""
a
b
c in[(a,>L),(b,>R)]
"""
		a = UGen(name="a")
		b = UGen(name="b")
		c = UGen(name="c")

		c.left  = a
		c.right = b

		self.assertEqual(self.transcript([a,b,c]),expected)


	def test_assigned_LR_lookup_connect(self):
		# 	c["left"]  = a
		# 	c["right"] = b
		expected = \
"""
a
b
c in[(a,>L),(b,>R)]
"""
		a = UGen(name="a")
		b = UGen(name="b")
		c = UGen(name="c")

		c["left"]  = a
		c["right"] = b

		self.assertEqual(self.transcript([a,b,c]),expected)


	def transcript(self,elements):
		f = StringIO()
		print >>f
		for x in elements:
			print >>f, x.transcript()
		return f.getvalue()


if __name__ == "__main__": unittest.main()
