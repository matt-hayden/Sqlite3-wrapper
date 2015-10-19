#!/usr/bin/env python3
import collections
import math

#
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
class ParametricBase(DescriptivesBase):
	@property
	def mean(self):
		_, m, _ = self.get_n_mean_var()
		return m
	@property
	def var(self): # sample variance
		_, _, v = self.get_n_mean_var()
		return v
	@property
	def stdev(self):
		return math.sqrt(self.var)
	def get_n_mean_var(self, sample=False):
		if self.freq:
			n, ts, ss = 0, 0., 0.
			for v, c in self.freq.items():
				n += c
				s = v*c
				ts += s
				ss += v*s
			if n <= 1:
				var = None
			elif sample:
				var = (ss - ts**2/n)/(n-1)
			else: # population
				var = (ss - ts**2/n)/n
			# var can be lower than 0 due to machine precision
			return n, ts/n, var if 0 < var else 0
		else:
			return None, None, None
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
		def preview(iterable):
			first = next(iterable)
			return ((first, first), iterable)
		if self.freq:
			(min, max), values = preview(iter(self.freq.keys()) )
			if values:
				for v in values:
					if v < min:
						min = v
					elif max < v:
						max = v
			return min, max, max-min
		else:
			return None, None, None
	def rel_freq(self):
		if self.freq:
			freqs = sorted(self.freq.items())
			n = sum(c for _, c in freqs)
			for v, c in freqs:
				yield v, float(c)/n
	def get_fns(self):
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
		assert 0 <= p <= 1
		if p == 0:
			return self.min
		elif p == 1:
			return self.max
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
		
import json
class Descriptives(ParametricBase, NonParametricBase):
	def get_descriptives(self):
		d = {}
		d['min'], d['first_quartile'], d['median'], d['third_quartile'], d['max'] = self.get_fns()
		n, d['mean'], var = self.get_n_mean_var()
		d['n'] = n
		d['var'] = var
		stdev = d['stdev'] = math.sqrt(var)
		d['stderr'] = stdev/math.sqrt(n-1) if 1 < n else None
		return d
	def to_json(self):
		d = self.get_descriptives()
		return json.dumps(d)
	def __str__(self):
		return self.to_json()
