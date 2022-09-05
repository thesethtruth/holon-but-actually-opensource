# import agentpy as ap

# Keep this example agent as blueprint
#  class MyAgent(ap.Agent):
#     def setup(self):
#         # Initialize an attribute with a parameter
#         self.my_attribute = self.p.my_parameter

#     def agent_method(self):
#         # Define custom actions here
#         pass
from array import array
import random
import numpy as np
from energyAssets import *


class GridNode:
    def __init__(
        self, nodeID, energyCarrier, capacity_kW, OL_netNodeType, parentNodeID
    ):
        # is called automatically when a new agent is created
        self.v_currentLoadElectricity_kW = 0
        self.v_currentLoadHeat_kW = 0
        self.v_currentLoadMethane_kW = 0
        self.v_currentLoadHydrogen_kW = 0
        self.nodeID = nodeID
        self.capacity_kW = capacity_kW
        self.energyCarrier = energyCarrier
        self.OL_netNodeType = OL_netNodeType
        self.parentNodeID = parentNodeID
        self.childConnections = []
        self.totalImportedEnergy_kWh = 0
        self.totalExportedEnergy_kWh = 0
        self.transportBuffer = None
        self.v_electricityDrawn_kWh = 0
        self.v_methaneDrawn_kWh = 0
        self.v_hydrogenDrawn_kWh = 0
        self.v_heatDrawn_kWh = 0
        self.v_electricityDelivered_kWh = 0
        self.v_methaneDelivered_kWh = 0
        self.v_hydrogenDelivered_kWh = 0
        self.v_heatDelivered_kWh = 0
        self.c_electricityFlows = []
        self.c_methaneFlows = []
        self.c_hydrogenFlows = []
        self.c_heatFlows = []

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
        self.c_electricityFlows.clear()
        self.c_methaneFlows.clear()
        self.c_hydrogenFlows.clear()
        self.c_heatFlows.clear()

        self.v_currentLoadElectricity_kW = 0
        self.v_currentLoadHeat_kW = 0
        self.v_currentLoadMethane_kW = 0
        self.v_currentLoadHydrogen_kW = 0
        # print("node reset!")

        for c in self.childConnections:
            # print("node ",self.nodeID, "energytype: ", self.energyCarrier, ", subconnection capacity: ", c.capacity_kW)
            if self.energyCarrier == "ELECTRICITY":
                # print("electricity node or connection!")
                currentLoad_kW = c.v_currentLoadElectricity_kW
                currentEnergy_kWh = c.v_currentLoadElectricity_kW * timestep_h
                self.v_currentLoadElectricity_kW += currentLoad_kW
                self.c_electricityFlows.append(currentLoad_kW)
                self.v_electricityDelivered_kWh += max(0, currentEnergy_kWh)
                self.v_electricityDrawn_kWh -= min(0, currentEnergy_kWh)
                self.totalImportedEnergy_kWh += max(0, currentEnergy_kWh)
                self.totalExportedEnergy_kWh -= min(0, currentEnergy_kWh)
            elif self.energyCarrier == "HEAT":
                # print("heat node or connection!")
                currentLoad_kW = c.v_currentLoadHeat_kW
                currentEnergy_kWh = c.v_currentLoadHeat_kW * timestep_h
                self.v_currentLoadHeat_kW += currentLoad_kW
                self.c_heatFlows.append(currentLoad_kW)
                self.v_heatDelivered_kWh += max(0, currentEnergy_kWh)
                self.v_heatDrawn_kWh -= min(0, currentEnergy_kWh)
                self.totalImportedEnergy_kWh += max(0, currentEnergy_kWh)
                self.totalExportedEnergy_kWh -= min(0, currentEnergy_kWh)

                v_powerfraction_fr = (
                    -self.v_currentLoadHeat_kW / self.transportBuffer.capacity_kW
                )
                self.transportBuffer.setPowerFraction(v_powerfraction_fr)
                self.transportBuffer.runAsset(timestep_h)
            elif self.energyCarrier == "METHANE":
                # print("methane node or connection!")
                currentLoad_kW = c.v_currentLoadMethane_kW
                currentEnergy_kWh = c.v_currentLoadMethane_kW * timestep_h
                self.v_currentLoadHeat_kW += currentLoad_kW
                self.c_methaneFlows.append(currentLoad_kW)
                self.v_methaneDelivered_kWh += max(0, currentEnergy_kWh)
                self.v_methaneDrawn_kWh -= min(0, currentEnergy_kWh)
                self.totalImportedEnergy_kWh += max(0, currentEnergy_kWh)
                self.totalExportedEnergy_kWh -= min(0, currentEnergy_kWh)
            elif self.energyCarrier == "HYDROGEN":
                # print("hydrogen node or connection!")
                currentLoad_kW = c.v_currentLoadHydrogen_kW
                currentEnergy_kWh = c.v_currentLoadHydrogen_kW * timestep_h
                self.v_currentLoadHydrogen_kW += currentLoad_kW
                self.c_hydrogenFlows.append(currentLoad_kW)
                self.v_hydrogenDelivered_kWh += max(0, currentEnergy_kWh)
                self.v_hydrogenDrawn_kWh -= min(0, currentEnergy_kWh)
                self.totalImportedEnergy_kWh += max(0, currentEnergy_kWh)
                self.totalExportedEnergy_kWh -= min(0, currentEnergy_kWh)

        # if self.nodeID == 'E1':
        #     print("Current HS grid load is " + str(self.v_currentLoadElectricity_kW) + ' kW, total imported electricity ' + str(self.totalImportedEnergy_kWh) + ' kWh, timestep ' +str(timestep_h))

    def setTransportBuffer(self, initialTemp_degC):
        self.transportBuffer = EA_StorageHeat(
            None,
            "Thermal Storage",
            1000,
            1e9,
            100,
            60,
            initialTemp_degC,
        )


# @jitclass
class GridConnection:
    def __init__(
        self,
        connectionID,
        capacity_kW,
        parentNodeElectricID,
        parentNodeHeatID,
        OL_ConnectionCategory,
        ownerID,
    ):
        # is called automatically when a new agent is created
        self.v_currentLoadElectricity_kW = 0
        self.v_currentLoadHeat_kW = 0
        self.v_currentLoadMethane_kW = 0
        self.v_currentLoadHydrogen_kW = 0
        self.v_electricityDrawn_kWh = 0
        self.v_methaneDrawn_kWh = 0
        self.v_hydrogenDrawn_kWh = 0
        self.v_heatDrawn_kWh = 0
        self.v_electricityDelivered_kWh = 0
        self.v_methaneDelivered_kWh = 0
        self.v_hydrogenDelivered_kWh = 0
        self.v_heatDelivered_kWh = 0
        self.connectionID = connectionID
        self.capacity_kW = capacity_kW
        # self.energyCarrier = energyCarrier
        self.OL_gridConnectionCategory = OL_ConnectionCategory
        self.parentNodeElectricID = parentNodeElectricID
        self.parentNodeHeatID = parentNodeHeatID
        self.connectedAssets = []
        self.EA_HeatingSystem = []
        self.EA_EV = []
        self.EA_ThermalStorage = []
        self.ownerID = ownerID

    def connectToParents(self, pop_gridNodes, pop_connectionOwners):
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

        x = [x for x in pop_connectionOwners if x.ID == self.ownerID]
        if bool(x):
            x = x[0]
            self.parentOwner = x
            x.connectToChild(self)

    # print('Connected gridConnection to electric parent node!')
    # if x.nodeID == self.parentNodeHeatID:

    # print('Connected gridConnection to heating parent node!')

    def connectToChild(self, connectedAsset: EnergyAsset):
        self.connectedAssets.append(connectedAsset)
        if connectedAsset.energyAssetType == "EV":
            self.EA_EV = connectedAsset
        elif (
            connectedAsset.energyAssetType == "Gas Burner"
            or connectedAsset.energyAssetType == "Delivery Set"
        ):
            self.EA_HeatingSystem = connectedAsset
        elif connectedAsset.energyAssetType == "Thermal Storage":
            self.EA_ThermalStorage = connectedAsset

    def initPowerFlowArray(self):
        self.powerFlows = np.zeros(
            [len(self.connectedAssets), 8]
        )  # Array of powerflows for all connected energyAssets
        if len(self.connectedAssets) == 0:
            print(
                "GridConnection " + str(self.connectionID) + "has no connected assets!"
            )

    def manageAssets(self, t, timestep_h, currentprofiles):
        # print("Managing EnergyAssets")
        if bool(self.EA_EV):
            # print(
            #     "Managing EV, next time at "
            #     + str(self.starttimes[self.tripNo] / 60)
            #     + " hours"
            # )
            if t > self.starttimes[self.tripNo] / 60 and self.EA_EV.available:
                self.EA_EV.startTrip()
            if t > self.endtimes[self.tripNo] / 60 and not self.EA_EV.available:
                self.EA_EV.endTrip(self.distances[self.tripNo])
                self.starttimes[self.tripNo] += 7 * 24 * 60
                self.endtimes[self.tripNo] += 7 * 24 * 60
                self.tripNo += 1
                if self.tripNo == self.nbTrips:
                    self.tripNo = 0
            self.EA_EV.setPowerFraction(self.capacity_kW / self.EA_EV.capacity_kW)
            # self.EA_EV.runAsset(timestep_h)
        if bool(self.EA_HeatingSystem) and bool(self.EA_ThermalStorage):
            if self.OL_gridConnectionCategory == "HOUSE":
                tempSetpoint_degC = 20
                houseTemp_degC = self.EA_ThermalStorage.storageTemp_degC
                self.EA_ThermalStorage.updateAmbientTemperature(
                    currentprofiles[OL_profiles.AMBIENTTEMP]
                )
                if houseTemp_degC < tempSetpoint_degC:
                    # //traceln("heatCapacity heatingSystem " + p_spaceHeatingAsset.p_energyAssetInstance.getHeatCapacity_kW());
                    powerDemand_kW = (
                        (tempSetpoint_degC - houseTemp_degC)
                        * (self.EA_ThermalStorage.heatCapacity_JpK)
                        / 3.6e6
                    )
                    self.EA_HeatingSystem.setPowerFraction(
                        powerDemand_kW / self.EA_HeatingSystem.capacity_kW
                    )
                    self.EA_ThermalStorage.setPowerFraction(
                        powerDemand_kW / self.EA_ThermalStorage.capacity_kW
                    )
                    # //traceln("Power fraction heating " + p_spaceHeatingAsset.v_powerFraction_fr);
                else:
                    self.EA_HeatingSystem.setPowerFraction(0)
                    self.EA_ThermalStorage.setPowerFraction(0)
                # self.EA_HeatingSystem.runAsset(timestep_h)
                # self.EA_ThermalStorage.runAsset(timestep_h)
                # if self.EA_HeatingSystem.energyAssetType == "Delivery Set":
                #     print(
                #         "house temp in house "
                #         + self.connectionID
                #         + " is "
                #         + str(houseTemp_degC)
                #         + ", heating system power fraction is "
                #         + str(self.EA_HeatingSystem.v_powerFraction_fr)
                #     )
            elif self.OL_gridConnectionCategory == "DISTRICTHEATING":
                tempSetpoint_degC = 70
                heatTransferToNetworkCoefficient_kWpK = 10
                storageTemp_degC = self.EA_ThermalStorage.storageTemp_degC
                heatTransferToNetwork_kW = (
                    max(
                        min(storageTemp_degC, tempSetpoint_degC)
                        - self.parentNodeHeat.transportBuffer.getStorageTemp(),
                        0,
                    )
                    * heatTransferToNetworkCoefficient_kWpK
                )
                # print(
                #     "District heating system is delivering "
                #     + str(heatTransferToNetwork_kW)
                #     + " kW heat to network. Storage temp is "
                #     + str(storageTemp_degC)
                #     + "degC, network temp is "
                #     + str(self.parentNodeHeat.transportBuffer.getStorageTemp())
                #     + " degC"
                # )
                self.EA_ThermalStorage.updateAmbientTemperature(
                    currentprofiles[OL_profiles.AMBIENTTEMP]
                )
                if storageTemp_degC < tempSetpoint_degC:
                    # //traceln("heatCapacity heatingSystem " + p_spaceHeatingAsset.p_energyAssetInstance.getHeatCapacity_kW());
                    powerDemand_kW = self.EA_HeatingSystem.capacity_kW
                    self.EA_HeatingSystem.setPowerFraction(
                        powerDemand_kW / self.EA_HeatingSystem.capacity_kW
                    )
                    self.EA_ThermalStorage.setPowerFraction(
                        (powerDemand_kW - heatTransferToNetwork_kW)
                        / self.EA_ThermalStorage.capacity_kW
                    )
                    # //traceln("Power fraction heating " + p_spaceHeatingAsset.v_powerFraction_fr);
                else:
                    self.EA_HeatingSystem.setPowerFraction(0)
                    self.EA_ThermalStorage.setPowerFraction(
                        -heatTransferToNetwork_kW / self.EA_ThermalStorage.capacity_kW
                    )

        for e in self.connectedAssets:
            if e.energyAssetType == "WINDMILL":
                e.setPowerFraction(currentprofiles[OL_profiles.WIND])

            if e.energyAssetType == "PHOTOVOLTAIC":
                e.setPowerFraction(currentprofiles[OL_profiles.SOLAR])

            if e.energyAssetType == "House_other_electricity":
                e.setPowerFraction(currentprofiles[OL_profiles.HOME_ELEC])

                # print(
                #     "HH other electricity demand "
                #     + str(e.v_powerFraction_fr * e.capacity_kW)
                #     + "kW"
                # )
            if e.energyAssetType == "House_hot_water":
                e.setPowerFraction(currentprofiles[OL_profiles.DHW])
                # e.runAsset()
                # print(
                #     "PV production household "
                #     + str(e.v_powerFraction_fr * e.capacity_kW)
                #     + "kW"
                # )
            e.runAsset(timestep_h)

        self.calculateEnergyBalance(timestep_h)

    def calculateEnergyBalance(self, timestep_h):
        # (
        #     self.v_currentLoadElectricity_kW,
        #     self.v_currentLoadHeat_kW,
        #     self.v_currentLoadMethane_kW,
        #     self.v_currentLoadHydrogen_kW,
        # ) = (0, 0, 0, 0)
        # for e in self.connectedAssets:
        #     # print("Looping over connected assets")
        #     self.v_currentLoadElectricity_kW += (
        #         e.v_currentConsumptionElectric_kW - e.v_currentProductionElectric_kW
        #     )
        #     self.v_currentLoadHeat_kW += (
        #         e.v_currentConsumptionHeat_kW - e.v_currentProductionHeat_kW
        #     )
        #     self.v_currentLoadMethane_kW += (
        #         e.v_currentConsumptionMethane_kW - e.v_currentProductionMethane_kW
        #     )
        #     self.v_currentLoadHydrogen_kW += (
        #         e.v_currentConsumptionHydrogen_kW - e.v_currentProductionHydrogen_kW
        #     )
        self.v_currentLoadElectricity_kW = sum(
            e.v_currentConsumptionElectric_kW - e.v_currentProductionElectric_kW
            for e in self.connectedAssets
        )
        self.v_currentLoadHeat_kW = sum(
            e.v_currentConsumptionHeat_kW - e.v_currentProductionHeat_kW
            for e in self.connectedAssets
        )
        self.v_currentLoadMethane_kW = sum(
            e.v_currentConsumptionMethane_kW - e.v_currentProductionMethane_kW
            for e in self.connectedAssets
        )
        self.v_currentLoadHydrogen_kW = sum(
            e.v_currentConsumptionHydrogen_kW - e.v_currentProductionHydrogen_kW
            for e in self.connectedAssets
        )

        self.v_electricityDrawn_kWh += (
            max(0, self.v_currentLoadElectricity_kW) * timestep_h
        )
        self.v_electricityDelivered_kWh += (
            -min(0, self.v_currentLoadElectricity_kW) * timestep_h
        )
        self.v_heatDrawn_kWh += max(0, self.v_currentLoadHeat_kW) * timestep_h
        self.v_heatDelivered_kWh += -min(0, self.v_currentLoadHeat_kW) * timestep_h
        self.v_methaneDrawn_kWh += max(0, self.v_currentLoadMethane_kW) * timestep_h
        self.v_methaneDelivered_kWh += (
            -min(0, self.v_currentLoadMethane_kW) * timestep_h
        )
        self.v_hydrogenDrawn_kWh += max(0, self.v_currentLoadHydrogen_kW) * timestep_h
        self.v_hydrogenDelivered_kWh += (
            -min(0, self.v_currentLoadHydrogen_kW) * timestep_h
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
    def __init__(self, ownerID, parentActorID, type):
        self.ID = ownerID
        self.ownedConnections = []
        self.parentActorID = parentActorID
        self.type = type
        self.balanceElectricity_eur = 0
        self.balanceHeat_eur = 0
        self.balanceMethane_eur = 0
        self.balanceHydrogen_eur = 0
        self.ElectricityContract = OL_EnergyContract.ELECTRICITYFIXED
        self.HeatContract = OL_EnergyContract.HEATFIXED
        self.MethaneContract = OL_EnergyContract.METHANEFIXED
        self.HydrogenContract = OL_EnergyContract.HYDROGENFIXED
        self.energyHolon = None
        self.energySupplier = None

    def connectToParents(self, pop_energyHolons, pop_energySuppliers):
        # for x in pop_gridNodes:
        #     if x.nodeID == self.parentNodeElectricID:
        x = [x for x in pop_energyHolons if x.ID == self.parentActorID]
        if bool(x):
            x = x[0]
            self.energyHolon = x
            self.energySupplier = x
            x.connectToChild(self)

        x = [x for x in pop_energySuppliers if x.ID == self.parentActorID]
        if bool(x):
            x = x[0]
            self.energySupplier = x
            x.connectToChild(self)

    # print('Connected gridConnection to electric parent node!')
    # if x.nodeID == self.parentNodeHeatID:

    # print('Connected gridConnection to heating parent node!')

    def connectToChild(self, gridConnection: GridConnection):
        self.ownedConnections.append(gridConnection)

    def updateFinances(self, timestep_h):
        # gather energy flows of owned connections
        (
            v_electricityVolume_kWh,
            v_heatVolume_kWh,
            v_methaneVolume_kWh,
            v_hydrogenVolume_kWh,
        ) = (0, 0, 0, 0)
        for c in self.ownedConnections:
            v_electricityVolume_kWh += c.v_currentLoadElectricity_kW * timestep_h
            v_heatVolume_kWh += c.v_currentLoadHeat_kW * timestep_h
            v_methaneVolume_kWh += c.v_currentLoadMethane_kW * timestep_h
            v_hydrogenVolume_kWh += c.v_currentLoadHydrogen_kW * timestep_h

        if bool(self.energySupplier):
            transactionCost_eur = self.energySupplier.doEnergyTransaction(
                v_electricityVolume_kWh, self.ElectricityContract
            )
            # print("transactionCost_eur " + str(transactionCost_eur))
            self.balanceElectricity_eur += transactionCost_eur
            transactionCost_eur = self.energySupplier.doEnergyTransaction(
                v_heatVolume_kWh, self.HeatContract
            )
            self.balanceHeat_eur += transactionCost_eur
            transactionCost_eur = self.energySupplier.doEnergyTransaction(
                v_methaneVolume_kWh, self.MethaneContract
            )
            self.balanceMethane_eur += transactionCost_eur
            transactionCost_eur = self.energySupplier.doEnergyTransaction(
                v_hydrogenVolume_kWh, self.HydrogenContract
            )
            self.balanceHydrogen_eur += transactionCost_eur
        else:
            print("Connection owner " + self.ID + " has no energy supplier!")

    def updateIncentives(self):
        pass


class EnergyHolon:
    def __init__(self, holonID, parentActorID):
        self.ID = holonID
        self.members = []
        self.energySupplier = None
        self.parentActorID = parentActorID
        self.electricityVolume_kWh = 0
        self.heatVolume_kWh = 0
        self.methaneVolume_kWh = 0
        self.hydrogenVolume_kWh = 0
        self.energyPassedThrough_kWh = 0
        self.electricityContract = OL_EnergyContract.ELECTRICITYVARIABLE

    def connectToChild(self, connectionOwner: ConnectionOwner):
        self.members.append(connectionOwner)

    def connectToParents(self, pop_energySuppliers):
        x = [x for x in pop_energySuppliers if x.ID == self.parentActorID]
        if bool(x):
            x = x[0]
            self.energySupplier = x
            x.connectToChild(self)
        else:
            print("HOLON wants to connect to non-existent energy-supplier!")

    def doEnergyTransaction(self, transactionVolume_kWh, contractType):
        transactionCostClient_eur = self.energySupplier.doEnergyTransaction(
            transactionVolume_kWh, contractType
        )
        # print(
        #     "Energy transaction through Holon! Volume "
        #     + str(transactionVolume_kWh)
        #     + " kWh"
        # )
        self.energyPassedThrough_kWh += transactionVolume_kWh
        return transactionCostClient_eur

    def updateFinances(self):
        pass


class EnergySupplier:
    def __init__(
        self,
        supplierID,
        fixedElectricityPrice_eurpkWh,
        fixedHeatPrice_eurpkWh,
        fixedMethanePrice_eurpkWh,
        fixedHydrogenPrice_eurpkWh,
        variableElectricityPriceOverNational_eurpkWh,
    ):
        self.ID = supplierID
        self.customers = []
        self.fixedElectricityPrice_eurpkWh = fixedElectricityPrice_eurpkWh
        self.fixedHeatPrice_eurpkWh = fixedHeatPrice_eurpkWh
        self.fixedMethanePrice_eurpkWh = fixedMethanePrice_eurpkWh
        self.fixedHydrogenPrice_eurpkWh = fixedHydrogenPrice_eurpkWh
        self.variableElectricityPriceOverNational_eurpkWh = (
            variableElectricityPriceOverNational_eurpkWh
        )
        self.currentVariableElectricityPrice_eurpkWh = 0
        self.currentBalanceElectricityClients_eur = 0
        self.currentBalanceElectricityNational_eur = 0
        self.currentBalanceHeatClients_eur = 0
        self.currentBalanceMethaneClients_eur = 0
        self.currentBalanceHydrogenClients_eur = 0
        self.totalElectricityBoughtFromClients_kWh = 0
        self.totalElectricitySoldToClients_kWh = 0
        self.currentNettElectricityVolume_kWh = 0
        self.totalElectricitySoldToNat_kWh = 0
        self.totalElectricityBoughtFromNat_kWh = 0

    def connectToChild(self, connectionOwner: ConnectionOwner):
        self.customers.append(connectionOwner)

    def doEnergyTransaction(self, transactionVolume_kWh, contractType):
        match contractType:
            case OL_EnergyContract.ELECTRICITYFIXED:
                transactionCostClient_eur = (
                    transactionVolume_kWh * self.fixedElectricityPrice_eurpkWh
                )
                # transactionCostNat_eur = (
                #     transactionVolume_kWh * self.currentVariableElectricityPrice_eurpkWh
                # )
                self.totalElectricityBoughtFromClients_kWh += -min(
                    0, transactionVolume_kWh
                )
                self.totalElectricitySoldToClients_kWh += max(0, transactionVolume_kWh)
                self.currentNettElectricityVolume_kWh += transactionVolume_kWh
                self.currentBalanceElectricityClients_eur += transactionCostClient_eur
                # self.currentBalanceElectricityNational_eur -= transactionCostNat_eur
                # print(
                #     "Basic fixed rate electricity transaction, volume "
                #     + str(transactionVolume_kWh)
                #     + " kWh"
                # )
            case OL_EnergyContract.ELECTRICITYVARIABLE:
                transactionCostClient_eur = transactionVolume_kWh * (
                    self.variableElectricityPriceOverNational_eurpkWh
                    + self.currentVariableElectricityPrice_eurpkWh
                )
                # transactionCostNat_eur = (
                #     transactionVolume_kWh * self.currentVariableElectricityPrice_eurpkWh
                # )
                self.totalElectricityBoughtFromClients_kWh += -min(
                    0, transactionVolume_kWh
                )
                self.totalElectricitySoldToClients_kWh += max(0, transactionVolume_kWh)
                self.currentNettElectricityVolume_kWh += transactionVolume_kWh
                self.currentBalanceElectricityClients_eur += transactionCostClient_eur
                # self.currentBalanceElectricityNational_eur -= transactionCostNat_eur
            case OL_EnergyContract.HEATFIXED:
                transactionCostClient_eur = (
                    transactionVolume_kWh * self.fixedHeatPrice_eurpkWh
                )
                self.currentBalanceHeatClients_eur += transactionCostClient_eur
            case OL_EnergyContract.METHANEFIXED:
                transactionCostClient_eur = (
                    transactionVolume_kWh * self.fixedMethanePrice_eurpkWh
                )
                self.currentBalanceMethaneClients_eur += transactionCostClient_eur
            case OL_EnergyContract.HYDROGENFIXED:
                transactionCostClient_eur = (
                    transactionVolume_kWh * self.fixedHydrogenPrice_eurpkWh
                )
                self.currentBalanceHydrogenClients_eur += transactionCostClient_eur
            case _:
                print("Incorrect contract type!")
        return transactionCostClient_eur

    def updateEnergyPrice(self, nat):
        self.currentVariableElectricityPrice_eurpkWh = (
            nat.getNationalElectricityPrice() / 1000
        )
        self.currentNettElectricityVolume_kWh = 0

    def updateFinances(self):
        self.totalElectricityBoughtFromNat_kWh += max(
            0, self.currentNettElectricityVolume_kWh
        )
        self.totalElectricitySoldToNat_kWh -= min(
            0, self.currentNettElectricityVolume_kWh
        )
        self.currentBalanceElectricityNational_eur -= (
            self.currentNettElectricityVolume_kWh
            * self.currentVariableElectricityPrice_eurpkWh
        )


class GridOperator:
    def __init__(self, operatorID):
        self.ID = operatorID


class NationalMarket:
    def __init__(self, currentNationalElectricityPrice_eurpkWh):
        self.currentNationalElectricityPrice_eurpkWh = (
            currentNationalElectricityPrice_eurpkWh
        )

    def updateNationalElectricityPrice(self, currentNationalElectricityPrice_eurpkWh):
        self.currentNationalElectricityPrice_eurpkWh = (
            currentNationalElectricityPrice_eurpkWh
        )

    def getNationalElectricityPrice(self):
        return self.currentNationalElectricityPrice_eurpkWh


def gridConnectionPowerflows(c: GridConnection, t, timestep_h, currentprofiles):
    c.manageAssets(t, timestep_h, currentprofiles)
    c.calculateEnergyBalance(timestep_h)
