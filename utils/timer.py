# -*- coding: utf-8 -*-

"""
Simple timer.
"""

from time import time

def timer(msg='', ls = ['', 0, 0], show_prev_output=True):
	"""
	Timer
	"""
	dt = 0

	if ls[1]:
		if show_prev_output:
			dt = time()-ls[1]
			print('{0}: {1:.4f} sec. (total time {2:.2f})'.format(
				ls[0], dt, time()-ls[2]))
	else:
		print('START TIMER {0}'.format(ls[0]))
		ls[2] = time()

	ls[0] = msg
	ls[1] = time()

	return dt
		
	
if __name__ == '__main__':
	
	timer("Test timer") # start
	timer() # reset
	
	
