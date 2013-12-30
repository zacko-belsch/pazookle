// "simple" test to verify the exact waveform through a band pass filter

//==========
// Chuck implementation of Marsaglia's KISS PRNG, as a noise generator.
//
// For details on the algorithm see the post here:
//   http://www.stata.com/statalist/archive/2005-04/msg00346.html
//
// The seeding here is NOT due to Marsaglia.
//==========

class Kiss32 extends Chugen
	{
	// bit masks to limit state values to 32 bits

	(1<<32) - 1 => int mask32;  // 0xFFFFFFFF
	(1<<31) - 1 => int mask31;  // 0x7FFFFFFF

	// set initial seed from current time;  it is not clear to what extent
	// this will work, because the time derived is the number of samples since
	// the chuck virtual machine was started;  using three different modulii
	// is probably useless since the derived time will be lower than any of
	// them;  for what it's worth, the modulii are all primes around the number
	// of samples per day

	(now / 1::samp) $ int => int start;
	(start % 69119989) & mask32 => int state1;
	(start % 69119957) & mask32 => int state2;
	(start % 69119951) & mask31 => int state3;

	// seed the state from a single seed value

	fun void seed(int seed)
		{
		seed & mask32 => state1;
		if (seed & mask32 == 0) 1             => state2;
		                   else seed & mask32 => state2;
		if (seed & mask31 == 0) 1             => state3;
		                   else seed & mask31 => state3;
		}

	// seed the state from three seed values

	fun void seed3(int seed1,int seed2,int seed3)
		{
		seed1 & mask32 => state1;
		if (seed2 & mask32 == 0) 1              => state2;
		                    else seed2 & mask32 => state2;
		if (seed3 & mask31 == 0) 1              => state3;
		                    else seed3 & mask31 => state3;
		}

	// generate the next random 32-bit value

	fun int rand32()
		{
		(69069 * state1 + 23606797) & mask32 => state1;
		(state2 ^ (state2 << 17))   & mask32 => state2;
		 state2 ^ (state2 >> 15)             => state2;
		(state3 ^ (state3 << 18))   & mask31 => state3;
		 state3 ^ (state3 >> 13)             => state3;
		return (state1 + state2 + state3) & mask32;
		}

	// tick -- generates random float between -1.0 and +1.0

	fun float tick(float in)
		{ return 2*(rand32()$float/mask32) - 1; }
	}

// the test

Kiss32 noise => BPF phil => WvOut waveOut => blackhole;

noise.seed(13013);

<<< "BPF defaults",
    "freq="+phil.freq(),
    "Q="+phil.Q() >>>;

600.0 => phil.freq;
7.0   => phil.Q;
3.0   => phil.gain;

me.dir() + "/test_BandPass.ck.wav" => waveOut.wavFilename;
3::second => now;
waveOut.closeFile;
