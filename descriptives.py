#!/usr/bin/env python3
import collections
import math

#
class DescriptivesError(Exception):
	pass
#
class DescriptivesBase:
	# requires freq={value:count...} with a .items() method, a-la
	# collections.Counters()
	def __init__(self):
		self.freq = collections.Counter()
	@property
	def count(self):
		if self.freq:
			return sum(c for _, c in self.freq.items())
	def rel_freq(self):
		if self.freq:
			freqs = sorted(self.freq.items())
			n = sum(c for _, c in freqs)
			for v, c in freqs:
				yield v, float(c)/n
class ParametricBase(DescriptivesBase):
	@property
	def mean(self):
		_, m, _ = self.get_parametrics()
		return m
	@property
	def var(self): # sample variance
		_, _, v = self.get_parametrics()
		return v
	@property
	def stdev(self):
		v = self.var
		return math.sqrt(v) if v else None
	def _get_parametric_sums(self):
		if self.freq:
			n, ts, ss = 0, 0., 0.
			for v, c in self.freq.items():
				n += c
				s = v*c
				ts += s
				ss += v*s
		return n, ts, ss
	def get_parametrics(self, parametric_sums=None, sample=True):
		if parametric_sums: # special parameter for accelerated mean and variance
			n, my_sum, my_sum2 = parametric_sums
		else:
			n, my_sum, my_sum2 = self._get_parametric_sums()
		if n <= 1:
			var = None
		elif sample:
			var = (my_sum2 - my_sum**2/n)/(n-1)
		else: # population
			var = (my_sum2 - my_sum**2/n)/n
		# var can be lower than 0 due to machine precision
		return n, my_sum/n, var if 0 < var else 0
class NonParametricBase(DescriptivesBase):
	@property
	def min(self):
		m, _, _ = self.get_min_max_range()
		return m
	@property
	def max(self):
		_, m, _ = self.get_min_max_range()
		return m
	@property
	def range(self):
		_, _, r = self.get_min_max_range()
		return r
	def get_min_max_range(self):
		def preview(iterable): # helper
			i = iter(iterable)
			first = next(i)
			return ((first, first), i)
		if self.freq:
			(min, max), values = preview(self.freq.keys() )
			if values:
				for v in values:
					if v < min:
						min = v
					elif max < v:
						max = v
			return min, max, max-min or None
		else:
			return None, None, None
	def get_fns(self):
		"""Five-number summary
		Returns:
			(min, 25th, median, 75th, max) of the distribution
		"""
		rel_freq = list(self.rel_freq())
		if rel_freq:
			points = [0.25, 0.5, 0.75]
			min, _ = rel_freq[0]
			max, _ = rel_freq[-1]
			cf, qs = 0, []
			k = points.pop(0)
			for v, f in rel_freq:
				if k < cf+f:
					qs.append(v)
					if points:
						k = points.pop(0)
					else:
						break
				cf += f
			return [min]+qs+[max]
		else:
			return [None]*5
	def get_percentile(self, p):
		"""
		Returns:
			x at p, (p_lower, p_upper)
			p_lower and p_upper are not guaranteed to be different
			An empty distribution will return None
		"""
		def panic(*args, **kwargs):
			raise DistributionError(args)
		assert 0 <= p <= 1
		if p == 0:
			return self.min, (p, p)
		if p == 1:
			return self.max, (p, p)
		rel_freq = self.rel_freq()
		if rel_freq:
			cf = 0
			for v, f in rel_freq:
				nf = cf+f
				if p < nf:
					return (v, (cf, nf))
				cf = nf
			return (v, (cf, 1.))
	@property
	def median(self):
		m, _ = self.get_percentile(0.5)
		return m
	@property
	def mode_freq(self):
		m, f = self.freq.most_common(1).pop()
	@property
	def mode(self):
		m, _ = self.mode_freq
		return m
		
class Descriptives(ParametricBase, NonParametricBase):
	def get_descriptives(self):
		d = {}
		ps = self._get_parametric_sums()
		n, d['sum'], d['sum_of_squares'] = ps
		if n:
			d['min'], d['first_quartile'], d['median'], d['third_quartile'], d['max'] = self.get_fns()
			d['n'], d['mean'], v = self.get_parametrics(ps)
			if v: # implies 1 < n
				assert 1 < n
				d['var'] = v
				stdev = d['stdev'] = math.sqrt(v)
				d['stderr'] = stdev/math.sqrt(n-1)
		return d
