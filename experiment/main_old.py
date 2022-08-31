import agentpy
from models import HolonBaseModel

parameters = {
    "agents": 100,
    "steps": 100,
    "seed": 42,
}

model = HolonBaseModel(parameters=parameters)
results = model.run()
