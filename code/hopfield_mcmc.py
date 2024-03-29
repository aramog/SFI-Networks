"""Uses Metropolis-Hastings to find an optimal graph given a certain set of states and # of edges."""
from graphs.Graph import *
from graphs.HopfieldGraph import *

from random_graphs import *
from hopfield_models import *
from hopfield_evaluation import *
from wiring_cost import *
from graph_utilities import *

import numpy as np
import random

def metropolis_hastings(patterns = None, num_edges = None, fp_threshold = 20, 
	max_iter = 1000, moves_per_iter = 1, beta = .3, hop_graph = None, alpha = .5,
	save_intermediate = False, save_freq = 10000, save_path = None):
	"""The main runner function of the file. Returns the result of running MCMC to find
	the optiminal graph topology given some set of patterns and number of edges."""
	def score(graph, cost_mean = 5000, cost_std = 3000, perf = None, cost = None):
		"""Given a graph, returns the performance metric which is a linear combination
		of retrievability (using some # of runs) and wiring cost. Gets the cost mean and std
		from simulation results over many graphs (might not be totally clean)."""
		if perf is None:
			perf = hopfield_performance(graph, retrievability_performance_metric, runs = 5)
		if cost is None:
			cost = wiring_cost_energy(graph)
		#first normalize the cost variable and negate so that higher is better.
		cost_norm = -1 * ((cost - cost_mean) / cost_std)
		return alpha * perf + (1 - alpha) * cost_norm
	
	def accept(curr, prop, beta = .9):
		"""Given an acceptance ratio, returns true if we should accept."""
		if prop > curr:
			#always accept when the proposal is better than current
			return True
		else:
			return False
		p = np.exp(-1 * beta * (prop / curr))
		return np.random.binomial(1, p) == 1
	
	#get initial random state
	if not hop_graph:
		graph = random_edges(len(patterns[0]), num_edges)
		hop_graph = HopfieldGraph(graph, patterns) #the running variable for the current optima
		hop_graph.train()
		#makes hop_graph pruned:
		#hop_graph = pruned_hopfield(patterns, num_edges)
	curr_score = score(hop_graph)
	old_score = curr_score #for fixed point checking
	
	while curr_score < .4:
		#makes sure we start at a reasonable state
		graph = random_edges(len(patterns[0]), num_edges)
		hop_graph = HopfieldGraph(graph, patterns) #the running variable for the current optima
		hop_graph.train()
		curr_score = score(hop_graph)
		print(curr_score)
	
	best_graph, best_score = hop_graph, curr_score #track the running best
	run_count, fp_count, away_from_best_count = 0, 0, 0 #count state vars
	perf_hist = [] #running history of retrievability of hop_graph
	cost_hist = [] #same for cost
	in_group_hist = []
	
	while run_count < max_iter:
		#generate a proposal by randomly swapping, adding, or removing an edge
		prop = hop_graph.copy()
		#prop_type = random.sample(range(3), 1)[0]
		prop_type = 0
		if prop_type == 0:
			#rewiring proposal
			for _ in range(moves_per_iter):
				i, j = random_edge(hop_graph)
				rewire(i, j, prop)
		elif prop_type == 1:
			#removal proposal
			for _ in range(moves_per_iter):
				i, j = random_edge(hop_graph)
				remove_edge(i, j, hop_graph)
		else:
			#adding proposal
			for _ in range(moves_per_iter):
				i, j = random_null_edge(hop_graph)
				add_edge(i, j, hop_graph)
		#moves to prop according to acceptance function
		prop_score = score(prop)
		if accept(curr_score, prop_score, beta):
			hop_graph = prop
			curr_score = prop_score
			fp_count = 0
		else:
			fp_count += 1
		curr_perf = hopfield_performance(hop_graph, retrievability_performance_metric, runs = 5)
		curr_cost = wiring_cost_energy(hop_graph)
		curr_score = score(hop_graph, perf = curr_perf, cost = curr_cost)
		perf_hist.append(curr_perf)
		cost_hist.append(curr_cost)
		if run_count % 5 == 0:
			#updates in group hist every 5 runs for runtime reasons
			in_group_hist.append(prop_in_group_edges(hop_graph))
		#updates best vars:
		if curr_score > best_score:
			best_score = curr_score
			best_graph = hop_graph
		print(str(run_count) + ", " + str(curr_score))
		run_count += 1
		#saves the graph to a json if save_intermediate and we're on the correct iteration
		if save_intermediate and run_count % save_freq == 0:
			filename = filepath + str(run_count) + ".txt"
			hop_graph.save(filename)
	return best_graph, [perf_hist, cost_hist, in_group_hist]
