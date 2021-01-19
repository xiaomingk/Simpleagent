Simple agent-based model

This simple agent-based model that simulates the investment decisions of power companies under climate policy. Each year, the agents choose the power plants that they expected to be profitable. There are 6 types of power plant that an agent can choose to invest-coal, gas, nuclear, wind and solar PV. The agents in the model are heterogenous in the way they perceive the investment risks, which is characterised by the hurdle rate each agent uses. In this simple model version, there are only three agents, using hurdle rates R1,R2 and R3.
The model starts with only coal and gas fire plants, but as there is a growing carbon tax imposed in this model (starts from 0 euro/ton and rises by 2 euro/ton and reaches 100 euro/ton and stays at 100 euro),agents will shift their investments to low-carbon technology and as a result, the model transits to a low carbon system.
This simple model is capable of simulating how does agents' risk aversion level impact their investment decisions, and in turn impacts the speed of the transition to a low-carbon power system.

This is a Python model written by Jinxi Yang at Chalmers University of Technology. Please contact her if you want to modify or cite the model. To be clear: the code in this repository has not yet been released under an open license.

Installation

Then copy/paste/type this (it may take a minute to build the package registry the first time):

pip install git+https://github.com/xiaomingk/Simpleagent.git

To simulate N years using self-defined hurdle rates:

import Agent

Agent.func_ABM(N, [R1,R2,R3],data_file)

In the parameter section, you can change the parameters, such as investment costs, fuels costs and carbon prices.
