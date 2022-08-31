from cmath import isnan
from types import NoneType

## ENUMs (OptionLists)
from enum import Enum


class OL_EnergyCarrier(Enum):
    ELECTRICITY = 1
    HEAT = 2
    METHANE = 3
    HYDROGEN = 4


class OL_EnergyContract(Enum):
    ELECTRICITYFIXED = 1
    ELECTRICITYVARIABLE = 2
    HEATFIXED = 3
    METHANEFIXED = 4
    HYDROGENFIXED = 5


class EnergyAsset:
    def __init__(self, AssetID, parentConnectionID, type, capacity_kW):
        self.AssetID = AssetID
        self.capacity_kW = capacity_kW
        self.parentConnectionID = parentConnectionID
        self.energyAssetType = type
        self.v_powerFraction_fr = 0
        self.v_currentConsumptionElectric_kW = 0
        self.v_currentProductionElectric_kW = 0
        self.v_currentConsumptionHeat_kW = 0
        self.v_currentProductionHeat_kW = 0
        self.v_currentConsumptionMethane_kW = 0
        self.v_currentProductionMethane_kW = 0
        self.v_currentConsumptionHydrogen_kW = 0
        self.v_currentProductionHydrogen_kW = 0
        self.energyUsed_kWh = 0

    def connectToParent(self, pop_gridConnection):
        x = [x for x in pop_gridConnection if x.connectionID == self.parentConnectionID]
        if bool(x):
            x = x[0]
            self.parentConnection = x
            x.connectToChild(self)
            # print("Parent agent " + str(x))
        # print(
        #     "Connected energyAsset "
        #     + self.AssetID
        #     + " to gridConnection "
        #     + self.parentConnection.connectionID
        # )

    def setPowerFraction(self, powerFraction_fr):
        self.v_powerFraction_fr = min(
            1, max(-1, powerFraction_fr)
        )  # Limited to range between -1 and 1

    def getEnergyUsed(self):
        return self.energyUsed_kWh


class EA_Consumption(EnergyAsset):
    def __init__(self, AssetID, parentConnectionID, type, capacity_kW) -> None:
        super().__init__(AssetID, parentConnectionID, type, capacity_kW)

    def runAsset(self):
        self.v_currentConsumptionElectric_kW = (
            self.v_powerFraction_fr * self.capacity_kW
        )


class EA_Production(EnergyAsset):
    def __init__(self, AssetID, parentConnectionID, type, capacity_kW) -> None:
        super().__init__(AssetID, parentConnectionID, type, capacity_kW)

    def runAsset(self):
        self.v_currentProductionElectric_kW = self.v_powerFraction_fr * self.capacity_kW


class EA_StorageElectric(EnergyAsset):
    def __init__(self, AssetID, parentConnectionID, type, capacity_kW) -> None:
        super().__init__(AssetID, parentConnectionID, type, capacity_kW)

    def runAsset(self):
        self.v_currentConsumptionElectric_kW = max(
            0, self.v_powerFraction_fr * self.capacity_kW
        )
        self.v_currentProductionElectric_kW = -min(
            0, self.v_powerFraction_fr * self.capacity_kW
        )


class EA_StorageHeat(EnergyAsset):
    def __init__(
        self,
        AssetID,
        parentConnectionID,
        type,
        capacity_kW,
        heatCapacity_JpK,
        lossFactor_WpK,
        initialTemp_degC,
        ambientTemp_degC,
    ) -> None:
        super().__init__(AssetID, parentConnectionID, type, capacity_kW)
        self.heatCapacity_JpK = heatCapacity_JpK
        self.lossFactor_WpK = lossFactor_WpK
        self.storageTemp_degC = initialTemp_degC
        self.ambientTemp_degC = ambientTemp_degC

    def runAsset(self, timestep_h):
        heatloss_kWh = (
            self.lossFactor_WpK
            * (self.storageTemp_degC - self.ambientTemp_degC)
            * timestep_h
            / 1000
        )
        self.energyUsed_kWh += heatloss_kWh
        energyDelta_kWh = (
            self.v_powerFraction_fr * self.capacity_kW * timestep_h
        ) - heatloss_kWh
        deltaTemp_degC = energyDelta_kWh / (self.heatCapacity_JpK / 3.6e6)
        self.storageTemp_degC += deltaTemp_degC
        self.v_currentProductionHeat_kW = -min(
            0, self.v_powerFraction_fr * self.capacity_kW
        )
        self.v_currentConsumptionHeat_kW = max(
            0, self.v_powerFraction_fr * self.capacity_kW
        )

    def getStorageTemp(self):
        return self.storageTemp_degC

    def updateAmbientTemperature(self, ambientTemperature_degC):
        self.ambientTemp_degC = ambientTemperature_degC


class EA_EV(EA_StorageElectric):
    def __init__(
        self,
        AssetID,
        parentConnectionID,
        type,
        capacity_kW,
        energyConsumption_kWhpkm,
        initialStateOfCharge_r,
        batteryCapacity_kWh,
    ) -> None:
        super().__init__(AssetID, parentConnectionID, type, capacity_kW)
        self.available = True
        self.energyConsumption_kWhpkm = energyConsumption_kWhpkm
        # self.energyUsed_kWh = 0
        self.stateOfCharge_r = initialStateOfCharge_r
        self.batteryCapacity_kWh = batteryCapacity_kWh
        self.v_powerFraction_fr = 1

    def runAsset(self, timestep_h):
        if self.available:
            deltaEnergy_kWh = self.v_powerFraction_fr * self.capacity_kW * timestep_h
            deltaEnergy_kWh = -min(
                -deltaEnergy_kWh, (self.stateOfCharge_r * self.batteryCapacity_kWh)
            )  # Prevent negative charge
            deltaEnergy_kWh = min(
                deltaEnergy_kWh, (1 - self.stateOfCharge_r) * self.batteryCapacity_kWh
            )  # Prevent overcharge

            discharge_kW = -deltaEnergy_kWh / timestep_h
            self.v_currentProductionElectric_kW = discharge_kW
            self.v_currentConsumptionElectric_kW = -discharge_kW
            self.stateOfCharge_r -= discharge_kW / self.batteryCapacity_kWh
            # if abs(discharge_kW) > 0:
            #     print("Charging EV with " + str(-discharge_kW) + " kW")
        else:
            self.v_currentProductionElectric_kW = 0
            self.v_currentConsumptionElectric_kW = 0

    def startTrip(self):
        if self.available:
            self.available = False
            # print("Leaving on trip!")
        else:
            print("Car is already away from home!")

    def endTrip(self, distance):
        if not self.available:
            self.available = True
            self.energyUsed_kWh += distance * self.energyConsumption_kWhpkm
            self.stateOfCharge_r -= (
                distance * self.energyConsumption_kWhpkm / self.batteryCapacity_kWh
            )
            # print(
            #     "Returned from trip! Used "
            #     + str(distance * self.energyConsumption_kWhpkm)
            #     + " kWh"
            # )
            if self.stateOfCharge_r < 0:
                print("Car returned home with empty battery!")

    def getCurrentStateOfChange(self):
        return self.stateOfCharge_r


class EA_Conversion(EnergyAsset):
    def __init__(
        self,
        AssetID,
        parentConnectionID,
        type,
        capacity_kW,
        efficiency_r,
        energyCarrierProduced: OL_EnergyCarrier,
        energyCarrierConsumed: OL_EnergyCarrier,
    ) -> None:
        super().__init__(AssetID, parentConnectionID, type, capacity_kW)

        self.eta_r = efficiency_r
        self.energyCarrierProduced = energyCarrierProduced
        self.energyCarrierConsumed = energyCarrierConsumed


class EA_GasBurner(EA_Conversion):
    def __init__(
        self,
        AssetID,
        parentConnectionID,
        type,
        capacity_kW,
        efficiency_r,
        energyCarrierProduced: OL_EnergyCarrier,
        energyCarrierConsumed: OL_EnergyCarrier,
    ) -> None:
        super().__init__(
            AssetID,
            parentConnectionID,
            type,
            capacity_kW,
            efficiency_r,
            energyCarrierProduced,
            energyCarrierConsumed,
        )

    def runAsset(self, timestep_h):
        self.v_currentProductionHeat_kW = self.capacity_kW * self.v_powerFraction_fr
        self.v_currentConsumptionMethane_kW = (
            self.v_currentProductionHeat_kW / self.eta_r
        )
        # print("Gas burner power fraction " + str(self.v_powerFraction_fr) + ", methane consumption " + str(self.v_currentConsumptionMethane_kW) + " kWh")
        self.energyUsed_kWh += timestep_h * (
            self.v_currentConsumptionMethane_kW - self.v_currentProductionHeat_kW
        )  # This represents losses!
