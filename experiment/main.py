import numpy as np
import pandas as pd
from agentsGH import *
from energyAssets import *
import time


t1 = time.time()
##############
## Load data from excells
# Load agents from config excell
configexcell = pd.ExcelFile("./db_backboneConfig_moreagents.xlsx")
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

# Load car trips
tripsexcell = pd.ExcelFile("./AlbatrossProcessedVehicleTrips.xlsx")
tripsarray = pd.read_excel(tripsexcell).to_numpy()


################
## Populate agent populations
pop_gridNodes = []
pop_gridConnections = []
pop_energyAssets = []
pop_connectionOwners = []
pop_energyHolons = []
pop_energySuppliers = []
pop_gridOperators = []

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
            df_gridConnections.owner_actor.array[idx],
        )
    )

    # Initialize default assets?
    if df_gridConnections.type.array[idx] == "HOUSE":
        # add EV
        pop_energyAssets.append(
            EA_EV(99, df_gridConnections.id.array[idx], "EV", 100, 0.2, 0.5, 60)
        )
        pop_gridConnections[idx].loadCarRides(tripsarray)

        # add thermal storage (ie. building thermal model)
        pop_energyAssets.append(
            EA_StorageHeat(
                99,
                df_gridConnections.id.array[idx],
                "Thermal Storage",
                100,
                1e7,
                100,
                20,
                df_profiles.ambientTemperature_degC.array[0],
            )
        )
        # add heating system
        pop_energyAssets.append(
            EA_GasBurner(
                99,
                df_gridConnections.id.array[idx],
                "Gas Burner",
                30,
                0.95,
                OL_EnergyCarrier.HEAT,
                OL_EnergyCarrier.METHANE,
            )
        )


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

#
for idx in df_actors.index.array:
    if df_actors.agenttype.array[idx] == "CONNECTIONOWNER":
        pop_connectionOwners.append(
            ConnectionOwner(
                df_actors.id.array[idx],
                df_actors.parent_actor.array[idx],
                df_actors.type.array[idx],
            )
        )
    if df_actors.agenttype.array[idx] == "ENERGYSUPPLIER":
        pop_energySuppliers.append(EnergySupplier(df_actors.id.array[idx]))

    if df_actors.agenttype.array[idx] == "ENERGYHOLON":
        pop_energyHolons.append(
            EnergyHolon(df_actors.id.array[idx], df_actors.parent_actor.array[idx])
        )

    if df_actors.agenttype.array[idx] == "GRIDOPERATOR":
        pop_gridOperators.append(GridOperator(df_actors.id.array[idx]))

# Make links between energyAssets and gridConnections
for e in pop_energyAssets:
    e.connectToParent(pop_gridConnections)

# Make links between gridConnections and gridNodes
for c in pop_gridConnections:
    c.connectToParents(pop_gridNodes, pop_connectionOwners)
    # print(x.parentNode.nodeID)

# Make links between gridConnections and connectionOwners
for o in pop_connectionOwners:
    o.connectToParents(pop_energyHolons, pop_energySuppliers)

# Make links between energyHolons and energySuppliers
for h in pop_energyHolons:
    h.connectToParents(pop_energySuppliers)

##############################################
## Simulate! Loop over timesteps
for t in np.arange(
    0, 24 * 7 * 52, timestep_h
):  ## Just 10 steps for now, for testing. Will be 8760 later of course.
    ## Update profiles
    df_currentprofiles = df_profiles.loc[[round(t)]]

    ## Propagate incentives

    ## Propagate powerflows
    # t0gC = time.time()
    for c in pop_gridConnections:
        c.manageAssets(t, timestep_h, df_currentprofiles)
        c.calculateEnergyBalance(timestep_h)
    # print(
    #     "Time spent on gridConnections in one timestep: "
    #     + str(time.time() - t0gC)
    #     + " seconds"
    # )

    # t0gN = time.time()
    for n in pop_gridNodes:
        n.calculateEnergyBalance(timestep_h)
    # print(
    #     "Time spent on gridNodes in one timestep: "
    #     + str(time.time() - t0gN)
    #     + " seconds"
    # )
    ## Financial transactions

    ## timestep print
    # print("Timestep at t=" + str(t) + " hours")

t2 = time.time()
print("Elapsed time " + str(t2 - t1))

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
