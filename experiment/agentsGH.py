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
        for x in pop_gridNodes:
            if x.nodeID == self.parentNodeID:
                self.parentNode = x
                x.connectToChild(self)
                # print('Connected gridNode to parent node!')

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
        for x in pop_gridNodes:
            if x.nodeID == self.parentNodeElectricID:
                self.parentNodeElectric = x
                x.connectToChild(self)
                # print('Connected gridConnection to electric parent node!')
            if x.nodeID == self.parentNodeHeatID:
                self.parentNodeHeat = x
                x.connectToChild(self)
                # print('Connected gridConnection to heating parent node!')

    def connectToChild(self, connectedAsset):
        self.connectedAssets.append(connectedAsset)

    def calculateEnergyBalance(self, timestep_h, df_profiles):
        self.v_currentLoadElectricity_kW = 0
        for e in self.connectedAssets:
            if e.energyAssetType == "WINDMILL":
                e.setPowerFraction(df_profiles.wind_e_prod_normalized.array[0])
                e.runAsset()
            if e.energyAssetType == "PHOTOVOLTAIC":
                e.setPowerFraction(df_profiles.solar_e_prod_normalized.array[0])
                e.runAsset()
            print("Looping over connected assets")
            self.v_currentLoadElectricity_kW += (
                e.v_currentConsumptionElectric_kW - e.v_currentProductionElectric_kW
            )
        if abs(self.v_currentLoadElectricity_kW) > 0:
            print(
                "Connection "
                + self.connectionID
                + " has electric load of "
                + str(self.v_currentLoadElectricity_kW)
                + " kW"
            )


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
