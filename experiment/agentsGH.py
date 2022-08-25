# agentsGH.py
# import agentpy as ap

# Keep this example agent as blueprint
#  class MyAgent(ap.Agent):
#     def setup(self):
#         # Initialize an attribute with a parameter
#         self.my_attribute = self.p.my_parameter

#     def agent_method(self):
#         # Define custom actions here
#         pass
import random
import numpy as np


class GridNode:
    def __init__(
        self, nodeID, energyCarrier, capacity_kW, OL_netNodeType, parentNodeID
    ):
        # is called automatically when a new agent is created
        self.v_currentLoadElectricity_kW = 0
        self.v_currentLoadHeat_kW = 0
        self.nodeID = nodeID
        self.capacity_kW = capacity_kW
        self.energyCarrier = energyCarrier
        self.OL_netNodeType = OL_netNodeType
        self.parentNodeID = parentNodeID
        self.childConnections = []
        self.totalImportedEnergy_kWh = 0
        self.totalExportedEnergy_kWh = 0

    def connectToParent(self, pop_gridNodes):
        x = [x for x in pop_gridNodes if x.nodeID == self.parentNodeID]
        if bool(x):
            x = x[0]
            self.parentNode = x
            x.connectToChild(self)

        # for x in pop_gridNodes:
        #     if x.nodeID == self.parentNodeID:
        #         # print('Connected gridNode to parent node!')

    def connectToChild(self, childNode):
        self.childConnections.append(childNode)

    def calculateEnergyBalance(self, timestep_h):
        self.v_currentLoadElectricity_kW = 0
        for c in self.childConnections:
            self.v_currentLoadElectricity_kW += c.v_currentLoadElectricity_kW
        self.totalImportedEnergy_kWh += max(
            0, self.v_currentLoadElectricity_kW * timestep_h
        )
        self.totalExportedEnergy_kWh -= min(
            0, self.v_currentLoadElectricity_kW * timestep_h
        )
        # if self.nodeID == 'E1':
        #     print("Current HS grid load is " + str(self.v_currentLoadElectricity_kW) + ' kW, total imported electricity ' + str(self.totalImportedEnergy_kWh) + ' kWh, timestep ' +str(timestep_h))


class GridConnection:
    def __init__(
        self,
        connectionID,
        capacity_kW,
        parentNodeElectricID,
        parentNodeHeatID,
        OL_ConnectionCategory,
    ):
        # is called automatically when a new agent is created
        self.v_currentLoadElectricity_kW = 0
        self.connectionID = connectionID
        self.capacity_kW = capacity_kW
        # self.energyCarrier = energyCarrier
        self.OL_gridConnectionCategory = OL_ConnectionCategory
        self.parentNodeElectricID = parentNodeElectricID
        self.parentNodeHeatID = parentNodeHeatID
        self.connectedAssets = []

    def connectToParents(self, pop_gridNodes):
        # for x in pop_gridNodes:
        #     if x.nodeID == self.parentNodeElectricID:
        x = [x for x in pop_gridNodes if x.nodeID == self.parentNodeElectricID]
        if bool(x):
            x = x[0]
            self.parentNodeElectric = x
            x.connectToChild(self)

        x = [x for x in pop_gridNodes if x.nodeID == self.parentNodeHeatID]
        if bool(x):
            x = x[0]
            self.parentNodeHeat = x
            x.connectToChild(self)

    # print('Connected gridConnection to electric parent node!')
    # if x.nodeID == self.parentNodeHeatID:

    # print('Connected gridConnection to heating parent node!')

    def connectToChild(self, connectedAsset):
        self.connectedAssets.append(connectedAsset)

    def manageAssets(self, t, timestep_h, df_profiles):
        # print("Managing EnergyAssets")
        for e in self.connectedAssets:
            if e.energyAssetType == "EV":
                # print(
                #     "Managing EV, next time at "
                #     + str(self.starttimes[self.tripNo] / 60)
                #     + " hours"
                # )
                if t > self.starttimes[self.tripNo] / 60 and e.available:
                    e.startTrip()
                if t > self.endtimes[self.tripNo] / 60 and not e.available:
                    e.endTrip(self.distances[self.tripNo])
                    self.starttimes[self.tripNo] += 7 * 24 * 60
                    self.endtimes[self.tripNo] += 7 * 24 * 60
                    self.tripNo += 1
                    if self.tripNo == self.nbTrips:
                        self.tripNo = 0
                e.setPowerFraction(self.capacity_kW / e.capacity_kW)
                e.runAsset(timestep_h)

            if e.energyAssetType == "WINDMILL":
                e.setPowerFraction(df_profiles.wind_e_prod_normalized.array[0])
                e.runAsset()
            if e.energyAssetType == "PHOTOVOLTAIC":
                e.setPowerFraction(df_profiles.solar_e_prod_normalized.array[0])
                e.runAsset()

    def calculateEnergyBalance(self, timestep_h):
        self.v_currentLoadElectricity_kW = 0
        for e in self.connectedAssets:
            # print("Looping over connected assets")
            self.v_currentLoadElectricity_kW += (
                e.v_currentConsumptionElectric_kW - e.v_currentProductionElectric_kW
            )
        # if abs(self.v_currentLoadElectricity_kW) > 0:
        #     print(
        #         "Connection "
        #         + self.connectionID
        #         + " has electric load of "
        #         + str(self.v_currentLoadElectricity_kW)
        #         + " kW"
        #     )

    def loadCarRides(self, tripsarray):
        self.starttimes = []
        self.endtimes = []
        self.distances = []

        rowNr = random.randint(1, 581)
        self.nbTrips = int(tripsarray[rowNr, 1])
        for i in np.arange(0, self.nbTrips):
            # print("Index " + str(i))
            self.starttimes.append(tripsarray[rowNr, 2 + i * 3])
            self.endtimes.append(tripsarray[rowNr, 3 + i * 3])
            self.distances.append(tripsarray[rowNr, 4 + i * 3])
        self.tripNo = 0
        # print("RowNr " + str(rowNr) + ", Car rides " + str(nbTrips))
        # print("Last trip distance is " + str(self.distances[nbTrips - 1]) + " km")


class ConnectionOwner:
    def __init__(self, ownerID):
        self.ID = ownerID


class EnergyHolon:
    def __init__(self, holonID):
        self.ID = holonID


class EnergySupplier:
    def __init__(self, supplierID):
        self.ID = supplierID


class GridOperator:
    def __init__(self, operatorID):
        self.ID = operatorID
