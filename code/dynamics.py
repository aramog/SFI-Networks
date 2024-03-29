import numpy as np

from graphs.Graph import *
from graphs.HopfieldGraph import *
from graphs.KuramotoGraph import *
from random_graphs import * 

"""
-- Each dynamics function takes a node as an argument.

-- Each update function takes a graph and dynamics function
as arguments and updates all node values accordingly.
"""
def majority_rule(node, threshold = .5, random = False):
	"""Given a node, update the node's
	value using simple majority rule."""
	num_yes = np.count_nonzero([v.val for v in node.in_edges])
	prop_yes = num_yes / len(node.in_edges)
	if not random:
		if prop_yes > threshold:
			node.val = 1
		else:
			node.val = 0
	else:
		node.val = np.random.binomial(1, prop_yes)

def random_majority_rule(node, threshold = .5):
	"""Runs random majority rule, can be passed into an update function."""
	majority_rule(node, threshold, True)

def asynch_update(graph, dynamic, iterations=1, print_states = False):
	"""Performs an asynchronus update in the order of nodes
	using the given dynamics function."""
	for _ in range(iterations):
		shuffled_nodes = graph.nodes.copy()
		random.shuffle(shuffled_nodes)
		for node in shuffled_nodes:
			dynamic(node)
		if print_states:
			print(graph.state())

def synch_update(graph, dynamic):
	"""Runs the dynamic on the graph's node values at the present state, and updates all values together."""
	pass

def fixed_point(graph, dynamic, update = asynch_update,
	max_iter = 1000, num_consec_threshold = 2, tolerance = .05):
	"""Runs the update rule with the given dynamic and graph
	till we reach a fixed state or max iterations is reached.
	Defines a fixed point as a state that is repeated threshold
	number of times. Returns false is no such state is found."""
	#have a boolean of if anyone changed instead of comparing states directly
	def soft_equals(lst1, lst2, tolerance):
		for i1, i2 in zip(lst1, lst2):
			if abs(i1 - i2) > tolerance:
				return False
		return True

	past, num_consec = graph.state(), 0
	for _ in range(max_iter):
		update(graph, dynamic)
		if soft_equals(graph.state(), past, tolerance):
			num_consec += 1
		else:
			num_consec = 0
		past = graph.state()
		if num_consec >= num_consec_threshold:
			return past
	return False
