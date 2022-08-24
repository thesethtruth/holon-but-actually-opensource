# agents.py
import agentpy as ap

# Keep this example agent as blueprint
class MyAgent(ap.Agent):
    def setup(self):
        # Initialize an attribute with a parameter
        self.my_attribute = self.p.my_parameter

    def agent_method(self):
        # Define custom actions here
        pass


class EnergyAsset(ap.Agent):
    def setup():
        # is called automatically when a new agent is created

        pass

    def transfer_energy():
        # should be called by the model on step or update

        pass