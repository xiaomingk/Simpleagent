Simple agent-based model

This simple agent-based model that simulates the transition to a renewable energy system.

This is a Python model written by Jinxi Yang at Chalmers University of Technology. Please contact her if you want to modify or cite the model. To be clear: the code in this repository has not yet been released under an open license.

Installation

Then copy/paste/type this (it may take a minute to build the package registry the first time):

pip install git+https://github.com/xiaomingk/Simpleagent.git

Running the model

To simulate 10 years using default parameters:

import Agent

Agent.Results()

Then examine the output variables capac and invest. Capacities are in MW with one row per year and one column per technology, in the order [wind, solar, nuclear, coal, gas]. Investments are listed with one row per plant investment, so several investments may take place each year. Investments with negative years represent the existing energy system at the beginning of the simulation at year 1.

