# models.py
import agentpy as ap
from agents import MyAgent

# Keep this example agent as blueprint
class MyModel(ap.Model):
    def setup(self):
        # Called at the start of the simulation
        self.agents = ap.AgentList(self, self.p.agents, MyAgent)

    def step(self):
        # Called at every simulation step
        self.agents.agent_method()  # Call a method for every agent

    def update(self):
        # Called after setup as well as after each step
        self.agents.record("my_attribute")  # Record variable

    def end(self):
        # Called at the end of the simulation
        self.report("my_reporter", 1)  # Report a simulation result


class HolonBaseModel(ap.Model):

    """A simple model that represents a electricity system from the HS/MS down to a residence"""

    def setup(self):
        # defines how many agents should be created at the beginning of the simulation.
        pass

    def step(self):
        # step calls all agents during each time-step to perform their wealth_transfer method.
        pass

    def update(self):
        # calculates and record the current Gini coefficient after each time-step.
        pass

    def end(self):
        # is called at the end of the simulation, we record the wealth of each agent.
        pass
