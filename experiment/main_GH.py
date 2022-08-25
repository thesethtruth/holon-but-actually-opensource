import numpy as np
import pandas as pd
from agentsGH import *
from energyAssets import *

##############
## Load data from excells
# Load agents from config excell
configexcell = pd.ExcelFile("./db_backboneConfig.xlsx")
df_gridNodes = pd.read_excel(configexcell, "config_netNodes")
df_gridConnections = pd.read_excel(configexcell, "config_netConnections")
df_actors = pd.read_excel(configexcell, "config_actors")
df_energyAssets = pd.read_excel(configexcell, "config_energyAssets")

# Load profiles from profiles excell
profilesexcell = pd.ExcelFile("./db_profiles.xlsx")
df_profiles = pd.read_excel(profilesexcell, "profiles")

# Load parameters from params excell
paramsexcell = pd.ExcelFile("./db_backboneParams.xlsx")
df_params = pd.read_excel(paramsexcell)
timestep_h = df_params.value[df_params.parameter == "p_timeStep_h"].values[0]
undergroundTemp_degC = df_params.value[
    df_params.parameter.array == "p_undergroundTemperature_degC"
].values[0]
# print('Underground temp ' + str(undergroundTemp_degC))


################
## Populate agent populations
pop_gridNodes = []
pop_gridConnections = []
pop_energyAssets = []


# Initialize gridNodes
for idx in df_gridNodes.index.array:
    pop_gridNodes.append(
        GridNode(
            df_gridNodes.id.array[idx],
            df_gridNodes.type.array[idx],
            df_gridNodes.capacity_kw.array[idx],
            df_gridNodes.type2.array[idx],
            df_gridNodes.parent.array[idx],
        )
    )

# Make links between gridNodes
for x in pop_gridNodes:
    x.connectToParent(pop_gridNodes)
    # print(x.parentNode.nodeID)


# Initialize gridConnections
for idx in df_gridConnections.index.array:
    pop_gridConnections.append(
        GridConnection(
            df_gridConnections.id.array[idx],
            df_gridConnections.capacity_kw.array[idx],
            df_gridConnections.parent_electric.array[idx],
            df_gridConnections.parent_heat.array[idx],
            df_gridConnections.type.array[idx],
        )
    )

    # Initialize default assets?

for idx in df_energyAssets.index.array:
    if df_energyAssets.type.array[idx] == "PRODUCTION":
        pop_energyAssets.append(
            EA_Production(
                df_energyAssets.id.array[idx],
                df_energyAssets.parent.array[idx],
                df_energyAssets.type2.array[idx],
                df_energyAssets.capacity_electric_kw.array[idx],
            )
        )
    if df_energyAssets.type.array[idx] == "CONSUMPTION":
        pop_energyAssets.append(
            EA_Consumption(
                df_energyAssets.id.array[idx],
                df_energyAssets.parent.array[idx],
                df_energyAssets.type2.array[idx],
                df_energyAssets.capacity_electric_kw.array[idx],
            )
        )
# Make links between energyAssets and gridConnections
for e in pop_energyAssets:
    e.connectToParent(pop_gridConnections)

# Make links between gridConnections and gridNodes
for x in pop_gridConnections:
    x.connectToParents(pop_gridNodes)
    # print(x.parentNode.nodeID)


##############################################
## Simulate! Loop over timesteps
for t in np.arange(
    0, 10, timestep_h
):  ## Just 10 steps for now, for testing. Will be 8760 later of course.
    ## Update profiles
    df_currentprofiles = df_profiles.loc[[t]]

    ## Propagate incentives

    ## Propagate powerflows
    for c in pop_gridConnections:
        c.calculateEnergyBalance(timestep_h, df_currentprofiles)

    for n in pop_gridNodes:
        n.calculateEnergyBalance(timestep_h)

    ## Financial transactions

    ## timestep print
    print("Timestep at t=" + str(t) + " hours")
print(
    "Total imported electricity in model "
    + str([x.totalImportedEnergy_kWh for x in pop_gridNodes if x.nodeID == "E1"])
    + " kWh"
)
print(
    "Total exported electricity in model "
    + str([x.totalExportedEnergy_kWh for x in pop_gridNodes if x.nodeID == "E1"])
    + " kWh"
)
