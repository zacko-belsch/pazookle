from pazookle.ugen import UGen

class KissNoise(UGen):
	"""Marsaglia's 32-bit KISS PRNG as a noise generator.

	For details on the algorithm see the post here:
	  www.stata.com/statalist/archive/2005-04/msg00346.html
	"""

	def __init__(self,seed=None,name=None,
	             bias=None,gain=None):
		super(KissNoise,self).__init__(inChannels=0,outChannels=1,name=name,
		                               bias=bias,gain=gain)

		if (seed != None): self.seed(seed)
		else:              self.seed3(69119989,69119957,69119951)

	def seed(self,seed):
		"""seed the state from a single seed value"""
		self.seed3(seed,seed,seed)

	def seed3(self,seed1,seed2,seed3):
		"""seed the state from three seed values"""
		self.state1 = seed1 & 0xFFFFFFFF
		if (seed2 & 0xFFFFFFFF == 0): self.state2 = 1
		else:                         self.state2 = seed2 & 0xFFFFFFFF
		if (seed3 & 0x7FFFFFFF == 0): self.state3 = 1
		else:                         self.state3 = seed3 & 0x7FFFFFFF

	def rand32(self):
		"""generate the next random 32-bit value"""
		self.state1 = (69069 * self.state1 + 23606797)    & 0xFFFFFFFF
		self.state2 = (self.state2 ^ (self.state2 << 17)) & 0xFFFFFFFF
		self.state2 =  self.state2 ^ (self.state2 >> 15)
		self.state3 = (self.state3 ^ (self.state3 << 18)) & 0x7FFFFFFF
		self.state3 =  self.state3 ^ (self.state3 >> 13)
		return (self.state1 + self.state2 + self.state3)  & 0xFFFFFFFF

	#-- tick handling --

	def tick(self):
		return 2*(float(self.rand32())/0xFFFFFFFF) - 1
