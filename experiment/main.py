import numpy as np
import pandas as pd
from agents import *
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
profiles_array = pd.read_excel(profilesexcell, "profiles").to_numpy()

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


nationalMarket = NationalMarket(0)
# Initialize gridNodes
# for idx in df_gridNodes.index.array:
#     pop_gridNodes.append(
#         GridNode(
#             df_gridNodes.id.array[idx],
#             df_gridNodes.type.array[idx],
#             df_gridNodes.capacity_kw.array[idx],
#             df_gridNodes.type2.array[idx],
#             df_gridNodes.parent.array[idx],
#         )
#     )

pop_gridNodes = [
    GridNode(
        df_gridNodes.id[idx],
        df_gridNodes.type[idx],
        df_gridNodes.capacity_kw[idx],
        df_gridNodes.type2[idx],
        df_gridNodes.parent[idx],
    )
    for idx in range(len(df_gridNodes))
]

# [
#     pop_gridNodes[idx].setTransportBuffer(df_params.value.array[1])
#     for idx in range(len(pop_gridNodes))
#     if pop_gridNodes[idx].energyCarrier == "HEAT"
# ]
[
    gridNode.setTransportBuffer(df_params.value.array[1])
    for gridNode in pop_gridNodes
    if gridNode.energyCarrier == "HEAT"
]

# for idx in df_gridNodes.index:
#     # pop_gridNodes.append(
#     #     GridNode(
#     #         df_gridNodes.id[idx],
#     #         df_gridNodes.type[idx],
#     #         df_gridNodes.capacity_kw[idx],
#     #         df_gridNodes.type2[idx],
#     #         df_gridNodes.parent[idx],
#     #     )
#     # )
#     if df_gridNodes.type[idx] == "HEAT":
#         pop_gridNodes[idx].transportBuffer = EA_StorageHeat(
#             None,
#             "Thermal Storage",
#             1000,
#             1e9,
#             100,
#             60,
#             df_params.value.array[1],
#         )

# # Make links between gridNodes
# for x in pop_gridNodes:
#     x.connectToParent(pop_gridNodes)
#     # print(x.parentNode.nodeID)
[gridNode.connectToParent(pop_gridNodes) for gridNode in pop_gridNodes]

# pop_gridConnections.append([
#         GridConnection(
#             df_gridConnections.id.array,
#             df_gridConnections.capacity_kw.array,
#             df_gridConnections.parent_electric.array,
#             df_gridConnections.parent_heat.array,
#             df_gridConnections.type.array,
#             df_gridConnections.owner_actor.array,
#         )]
#     )


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
        # add house appliances consumption asset
        pop_energyAssets.append(
            EA_Consumption(
                df_gridConnections.id.array[idx],
                "House_other_electricity",
                2,
                OL_EnergyCarrier.ELECTRICITY,
            )
        )
        # Add DHW consumption asset
        pop_energyAssets.append(
            EA_Consumption(
                df_gridConnections.id.array[idx],
                "House_hot_water",
                10,
                OL_EnergyCarrier.HEAT,
            )
        )
        # add solar panels
        pop_energyAssets.append(
            EA_Production(
                df_gridConnections.id.array[idx],
                "PHOTOVOLTAIC",
                3,
                OL_EnergyCarrier.ELECTRICITY,
            )
        )
        # add EV
        pop_energyAssets.append(
            EA_EV(df_gridConnections.id.array[idx], "EV", 100, 0.2, 0.5, 80)
        )
        pop_gridConnections[idx].loadCarRides(tripsarray)

        # add thermal storage (ie. building thermal model)
        pop_energyAssets.append(
            EA_StorageHeat(
                df_gridConnections.id.array[idx],
                "Thermal Storage",
                100,
                1e7,
                100,
                20,
                profiles_array[0, OL_profiles.AMBIENTTEMP],
            )
        )
        # add heating system
        if str(df_gridConnections.parent_heat[idx]) == "nan":
            # print(
            #     "Adding gas burner to gridConnection "
            #     + df_gridConnections.id.array[idx]
            # )
            pop_energyAssets.append(
                EA_GasBurner(
                    df_gridConnections.id.array[idx],
                    "Gas Burner",
                    30,
                    0.95,
                )
            )
        else:
            pop_energyAssets.append(
                EA_HeatDeliverySet(
                    df_gridConnections.id.array[idx],
                    "Delivery Set",
                    10,
                    0.99,
                )
            )
            # print(
            #     "Adding heat delivery set to gridConnection "
            #     + df_gridConnections.id.array[idx]
            # )
    if df_gridConnections.type.array[idx] == "DISTRICTHEATING":
        # add thermal storage (ie. thermal storage for central heating)
        pop_energyAssets.append(
            EA_StorageHeat(
                df_gridConnections.id.array[idx],
                "Thermal Storage",
                1000,
                1e8,
                1000,
                60,
                profiles_array[0, OL_profiles.AMBIENTTEMP],
            )
        )
        # add heating system

        pop_energyAssets.append(
            EA_GasBurner(
                df_gridConnections.id.array[idx],
                "Gas Burner",
                300,
                0.95,
            )
        )

for idx in df_energyAssets.index.array:
    if df_energyAssets.type.array[idx] == "PRODUCTION":
        pop_energyAssets.append(
            EA_Production(
                # df_energyAssets.id.array[idx],
                df_energyAssets.parent.array[idx],
                df_energyAssets.type2.array[idx],
                df_energyAssets.capacity_electric_kw.array[idx],
                OL_EnergyCarrier.ELECTRICITY,
            )
        )
    if df_energyAssets.type.array[idx] == "CONSUMPTION":
        pop_energyAssets.append(
            EA_Consumption(
                # df_energyAssets.id.array[idx],
                df_energyAssets.parent.array[idx],
                df_energyAssets.type2.array[idx],
                df_energyAssets.capacity_electric_kw.array[idx],
                OL_EnergyCarrier.ELECTRICITY,
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
        pop_energySuppliers.append(
            EnergySupplier(df_actors.id.array[idx], 0.21, 0.1, 0.05, 0.3, 0.17)
        )

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
    # c.initPowerFlowArray()  # Prepare power-flow array


# Make links between gridConnections and connectionOwners
for o in pop_connectionOwners:
    o.connectToParents(pop_energyHolons, pop_energySuppliers)

# Make links between energyHolons and energySuppliers
for h in pop_energyHolons:
    h.connectToParents(pop_energySuppliers)

t_init = time.time() - t1
print("Initialisation time ".join([str(t_init), " seconds"]))
# df_profilecolumns = df_profiles.columns
##############################################cd
## Simulate! Loop over timesteps
for t in np.arange(
    0, 24 * 7 * 52, timestep_h
):  ## Just 10 steps for now, for testing. Will be 8760 later of course.
    ## Update profiles
    currentprofiles = profiles_array[t, :]

    ## Propagate incentives
    nationalMarket.updateNationalElectricityPrice(
        currentprofiles[OL_profiles.ELEC_SPOTMARKET]
    )

    for e in pop_energySuppliers:
        e.updateEnergyPrice(nationalMarket)

    ## Propagate powerflows
    for c in pop_gridConnections:
        c.manageAssets(t, timestep_h, currentprofiles)
        c.calculateEnergyBalance(timestep_h)  # bootstrapped in manageAssets function

    for n in pop_gridNodes:
        n.calculateEnergyBalance(timestep_h)

    ## Financial transactions
    for o in pop_connectionOwners:
        o.updateFinances(timestep_h)

    for e in pop_energyHolons:
        e.updateFinances()

    for e in pop_energySuppliers:
        e.updateFinances()

    ## timestep print
    # print("Timestep at t=" + str(t) + " hours")

    # [e.updateEnergyPrice(nationalMarket) for e in pop_energySuppliers]

    # ## Propagate powerflows
    # # t0gC = time.time()
    # [c.manageAssets(t, timestep_h, currentprofiles) for c in pop_gridConnections]
    # # c.calculateEnergyBalance(timestep_h)

    # # [pop_gridConnections[i].manageAssets(t, timestep_h, df_currentprofiles) for i in range(len(pop_gridConnections))] # Not faster than normal loop...
    # # [pop_gridConnections[i].calculateEnergyBalance(timestep_h) for i in range(len(pop_gridConnections))] # Not faster than normal loop...

    # [n.calculateEnergyBalance(timestep_h) for n in pop_gridNodes]

    # [o.updateFinances(timestep_h) for o in pop_connectionOwners]

    # [e.updateFinances() for e in pop_energyHolons]

    # [e.updateFinances() for e in pop_energySuppliers]

    ## timestep print
    # print("Timestep at t=" + str(t) + " hours")

t2 = time.time()
print("Elapsed time " + str(t2 - t1))

print(
    "Total imported electricity in model "
    + str([x.v_electricityDelivered_kWh for x in pop_gridNodes if x.nodeID == "E1"])
    + " kWh"
)
print(
    "Total exported electricity in model "
    + str([x.v_electricityDrawn_kWh for x in pop_gridNodes if x.nodeID == "E1"])
    + " kWh"
)

print(
    "Total imported heat in model "
    + str([x.v_heatDelivered_kWh for x in pop_gridNodes if x.energyCarrier == "HEAT"])
    + " kWh"
)
print(
    "Total exported heat in model "
    + str([x.v_heatDrawn_kWh for x in pop_gridNodes if x.energyCarrier == "HEAT"])
    + " kWh"
)
