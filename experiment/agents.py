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
#from fcntl import F_FULLFSYNC
from genericpath import exists
import random
from typing import List
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
        self.transportBuffer = ''
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
        #print("node reset!")

        for c in self.childConnections:
            #print("node ",self.nodeID, "energytype: ", self.energyCarrier, ", subconnection capacity: ", c.capacity_kW)
            if self.energyCarrier == "ELECTRICITY":
                #print("electricity node or connection!")
                currentLoad_kW = c.v_currentLoadElectricity_kW
                currentEnergy_kWh = c.v_currentLoadElectricity_kW * timestep_h
                self.v_currentLoadElectricity_kW += currentLoad_kW
                self.c_electricityFlows.append(currentLoad_kW)
                self.v_electricityDelivered_kWh += max(0, currentEnergy_kWh)
                self.v_electricityDrawn_kWh -=  min(0, currentEnergy_kWh)
                self.totalImportedEnergy_kWh += max(0, currentEnergy_kWh)
                self.totalExportedEnergy_kWh -= min(0, currentEnergy_kWh)
            elif self.energyCarrier == "HEAT":                    
                #print("heat node or connection!")
                currentLoad_kW = c.v_currentLoadHeat_kW
                currentEnergy_kWh = c.v_currentLoadHeat_kW * timestep_h
                self.v_currentLoadHeat_kW += currentLoad_kW
                self.c_heatFlows.append(currentLoad_kW)
                self.v_heatDelivered_kWh += max(0, currentEnergy_kWh)
                self.v_heatDrawn_kWh -=  min(0, currentEnergy_kWh)  
                self.totalImportedEnergy_kWh += max(0, currentEnergy_kWh)
                self.totalExportedEnergy_kWh -= min(0, currentEnergy_kWh)
            elif self.energyCarrier == "METHANE":                    
                #print("methane node or connection!")
                currentLoad_kW = c.v_currentLoadMethane_kW
                currentEnergy_kWh = c.v_currentLoadMethane_kW * timestep_h
                self.v_currentLoadHeat_kW += currentLoad_kW
                self.c_methaneFlows.append(currentLoad_kW)
                self.v_methaneDelivered_kWh += max(0, currentEnergy_kWh)
                self.v_methaneDrawn_kWh -=  min(0, currentEnergy_kWh)  
                self.totalImportedEnergy_kWh += max(0, currentEnergy_kWh)
                self.totalExportedEnergy_kWh -= min(0, currentEnergy_kWh)
            elif self.energyCarrier == "HYDROGEN":                    
                #print("hydrogen node or connection!")
                currentLoad_kW = c.v_currentLoadHydrogen_kW
                currentEnergy_kWh = c.v_currentLoadHydrogen_kW * timestep_h
                self.v_currentLoadHydrogen_kW += currentLoad_kW
                self.c_hydrogenFlows.append(currentLoad_kW)
                self.v_hydrogenDelivered_kWh += max(0, currentEnergy_kWh)
                self.v_hydrogenDrawn_kWh -=  min(0, currentEnergy_kWh)  
                self.totalImportedEnergy_kWh += max(0, currentEnergy_kWh)
                self.totalExportedEnergy_kWh -= min(0, currentEnergy_kWh)                  

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

        if connectedAsset.energyAssetType == "EV":
            self.EA_EV = connectedAsset
        elif connectedAsset.energyAssetType == "Gas Burner":
            self.EA_HeatingSystem = connectedAsset
        elif connectedAsset.energyAssetType == "Thermal Storage":
            self.EA_ThermalStorage = connectedAsset
        else:
            self.connectedAssets.append(connectedAsset)

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
            # print(
            #     "house temp in house "
            #     + self.connectionID
            #     + " is "
            #     + str(houseTemp_degC)
            #     + ", heating system power fraction is "
            #     + str(self.EA_HeatingSystem.v_powerFraction_fr)
            # )

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


class EnergySupplier:
    def __init__(self, supplierID):
        self.ID = supplierID
        self.customers = []

    def connectToChild(self, connectionOwner: ConnectionOwner):
        self.customers.append(connectionOwner)

    def doEnergyTransaction(self, transactionVolume_kWh, contractType):
        return 0


class GridOperator:
    def __init__(self, operatorID):
        self.ID = operatorID
