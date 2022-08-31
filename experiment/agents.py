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
from ast import match_case
from genericpath import exists
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
        ownerID,
    ):
        # is called automatically when a new agent is created
        self.v_currentLoadElectricity_kW = 0
        self.v_currentLoadHeat_kW = 0
        self.v_currentLoadMethane_kW = 0
        self.v_currentLoadHydrogen_kW = 0
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
        self.electricityDrawn_kWh = 0
        self.electricityDelivered_kWh = 0
        self.heatDrawn_kWh = 0
        self.heatDelivered_kWh = 0
        self.methaneDrawn_kWh = 0
        self.methaneDelivered_kWh = 0
        self.hydrogenDrawn_kWh = 0
        self.hydrogenDelivered_kWh = 0

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

        elif connectedAsset.energyAssetType == "Gas Burner":
            self.EA_HeatingSystem = connectedAsset

        elif connectedAsset.energyAssetType == "Thermal Storage":
            self.EA_ThermalStorage = connectedAsset

    def manageAssets(self, t, timestep_h, df_profiles):
        # print("Managing EnergyAssets")
        for e in self.connectedAssets:
            if e.energyAssetType == "WINDMILL":
                e.setPowerFraction(df_profiles.wind_e_prod_normalized.array[0])
                e.runAsset()
            if e.energyAssetType == "PHOTOVOLTAIC":
                e.setPowerFraction(df_profiles.solar_e_prod_normalized.array[0])
                e.runAsset()

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
            self.EA_EV.runAsset(timestep_h)
        if bool(self.EA_HeatingSystem) and bool(self.EA_ThermalStorage):
            tempSetpoint_degC = 20
            houseTemp_degC = self.EA_ThermalStorage.storageTemp_degC
            self.EA_ThermalStorage.updateAmbientTemperature(
                df_profiles.ambientTemperature_degC.array[0]
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
            self.EA_HeatingSystem.runAsset(timestep_h)
            self.EA_ThermalStorage.runAsset(timestep_h)
            print(
                "house temp in house "
                + self.connectionID
                + " is "
                + str(houseTemp_degC)
                + ", heating system power fraction is "
                + str(self.EA_HeatingSystem.v_powerFraction_fr)
            )

    def calculateEnergyBalance(self, timestep_h):
        self.v_currentLoadElectricity_kW = 0
        self.v_currentLoadHeat_kW = 0
        self.v_currentLoadMethane_kW = 0
        self.v_currentLoadHydrogen_kW = 0
        for e in self.connectedAssets:
            # print("Looping over connected assets")
            self.v_currentLoadElectricity_kW += (
                e.v_currentConsumptionElectric_kW - e.v_currentProductionElectric_kW
            )
            self.v_currentLoadHeat_kW += (
                e.v_currentConsumptionHeat_kW - e.v_currentProductionHeat_kW
            )
            self.v_currentLoadMethane_kW += (
                e.v_currentConsumptionMethane_kW - e.v_currentProductionMethane_kW
            )
            self.v_currentLoadHydrogen_kW += (
                e.v_currentConsumptionHydrogen_kW - e.v_currentProductionHydrogen_kW
            )

        self.electricityDrawn_kWh += max(
            0, self.v_currentLoadElectricity_kW * timestep_h
        )
        self.electricityDelivered_kWh -= min(
            0, self.v_currentLoadElectricity_kW * timestep_h
        )
        self.heatDrawn_kWh += max(0, self.v_currentLoadHeat_kW * timestep_h)
        self.heatDelivered_kWh -= min(0, self.v_currentLoadHeat_kW * timestep_h)
        self.methaneDrawn_kWh += max(0, self.v_currentLoadMethane_kW * timestep_h)
        self.methaneDelivered_kWh -= min(0, self.v_currentLoadMethane_kW * timestep_h)
        self.hydrogenDrawn_kWh += max(0, self.v_currentLoadHydrogen_kW * timestep_h)
        self.hydrogenDelivered_kWh -= min(0, self.v_currentLoadHydrogen_kW * timestep_h)
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
        v_electricityVolume_kWh = 0
        v_heatVolume_kWh = 0
        v_methaneVolume_kWh = 0
        v_hydrogenVolume_kWh = 0
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
                transactionCostNat_eur = (
                    transactionVolume_kWh * self.currentVariableElectricityPrice_eurpkWh
                )
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
                transactionCostNat_eur = (
                    transactionVolume_kWh * self.currentVariableElectricityPrice_eurpkWh
                )
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
        self.currentVariableElectricityPrice_eurpkWh = nat.getNationalElectricityPrice()

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


def gridConnectionPowerflows(c: GridConnection, t, timestep_h, df_currentprofiles):
    c.manageAssets(t, timestep_h, df_currentprofiles)
    c.calculateEnergyBalance(timestep_h)
