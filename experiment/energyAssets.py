from cmath import isnan
from types import NoneType


class EnergyAsset:
    def __init__(self, AssetID, parentConnectionID, type, capacity_kW):
        self.AssetID = AssetID
        self.capacity_kW = capacity_kW
        self.parentConnectionID = parentConnectionID
        self.energyAssetType = type
        self.v_powerFraction_fr = 0
        self.v_currentConsumptionElectric_kW = 0
        self.v_currentProductionElectric_kW = 0

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
        self.v_powerFraction_fr = powerFraction_fr


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
        self.v_currentProductionElectric_kW = self.v_powerFraction_fr * self.capacity_kW


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
        self.energyUsed_kWh = 0
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
            if abs(discharge_kW) > 0:
                print("Charging EV with " + str(-discharge_kW) + " kW")
        else:
            self.v_currentProductionElectric_kW = 0
            self.v_currentConsumptionElectric_kW = 0

    def startTrip(self):
        if self.available:
            self.available = False
            print("Leaving on trip!")
        else:
            print("Car is already away from home!")

    def endTrip(self, distance):
        if not self.available:
            self.available = True
            self.energyUsed_kWh += distance * self.energyConsumption_kWhpkm
            self.stateOfCharge_r -= (
                distance * self.energyConsumption_kWhpkm / self.batteryCapacity_kWh
            )
            print(
                "Returned from trip! Used "
                + str(distance * self.energyConsumption_kWhpkm)
                + " kWh"
            )
            if self.stateOfCharge_r < 0:
                print("Car returned home with empty battery!")

    def getCurrentStateOfChange(self):
        return self.stateOfCharge_r
