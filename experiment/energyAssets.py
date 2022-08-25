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
        for x in pop_gridConnection:
            if x.connectionID == self.parentConnectionID:
                self.parentConnection = x
                x.connectToChild(self)
                # print(
                #     "Connected energyAsset "
                #     + self.AssetID
                #     + " to gridConnection "
                #     + self.parentConnection.connectionID
                # )


class EA_Consumption(EnergyAsset):
    def __init__(self, AssetID, parentConnectionID, type, capacity_kW) -> None:
        super().__init__(AssetID, parentConnectionID, type, capacity_kW)

    def setPowerFraction(self, powerFraction_fr):
        self.v_powerFraction_fr = powerFraction_fr

    def runAsset(self):
        self.v_currentConsumptionElectric_kW = (
            self.v_powerFraction_fr * self.capacity_kW
        )


class EA_Production(EnergyAsset):
    def __init__(self, AssetID, parentConnectionID, type, capacity_kW) -> None:
        super().__init__(AssetID, parentConnectionID, type, capacity_kW)

    def setPowerFraction(self, powerFraction_fr):
        self.v_powerFraction_fr = powerFraction_fr

    def runAsset(self):
        self.v_currentProductionElectric_kW = self.v_powerFraction_fr * self.capacity_kW
