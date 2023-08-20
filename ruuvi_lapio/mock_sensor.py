import time
import random
from typing import Callable, List, Union

from ruuvitag_sensor.ruuvi import MacAndSensorData, RunFlag


class MockSensor:
    def __init__(self):
        # Generate random mac address
        self.mac = "".join(random.choice("0123456789ABCDEF") for _ in range(12)).lower()
        self.battery = random.uniform(2.0, 3.0)
        self.pressure = random.uniform(1000.0, 1010.0)
        self.measurement_sequence_number = random.randint(1000, 10000)

        self.temperature = random.uniform(-20.0, 25.0)
        self.acceleration = random.uniform(1000.0, 2050.0)
        self.acceleration_z = self.acceleration
        self.acceleration_y = random.randint(-10, 10)
        self.acceleration_x = random.randint(-10, 10)
        self.humidity = random.uniform(20.0, 80.0)
        self.tx_power = random.randint(0, 10)
        self.movement_counter = random.randint(0, 100)
        self.rssi = random.randint(-100, 0)

    def update_data(self):
        self.temperature += max(-25.0, min(80.0, random.uniform(-0.05, 0.05)))
        self.humidity += max(0.0, min(90.0, random.uniform(-0.05, 0.05)))
        self.movement_counter += 1 if random.randint(0, 10) == 0 else 0
        self.pressure += random.uniform(-0.01, 0.01)
        self.measurement_sequence_number += 1

    def get_reading(self) -> Union[MacAndSensorData, None]:
        if random.randint(0, 3) == 0:
            self.measurement_sequence_number += 1
            return None
        self.update_data()
        return [
            self.mac,
            {
                "data_format": 5,
                "battery": self.battery,
                "pressure": self.pressure,
                "mac": self.mac,
                "measurement_sequence_number": self.measurement_sequence_number,
                "acceleration_z": self.acceleration_z,
                "acceleration": self.acceleration,
                "temperature": self.temperature,
                "acceleration_y": self.acceleration_y,
                "acceleration_x": self.acceleration_x,
                "humidity": self.humidity,
                "tx_power": self.tx_power,
                "movement_counter": self.movement_counter,
                "rssi": self.rssi,
            },
        ]


class MockSensorReader:
    def __init__(self, count: int = 3):
        self.sensors = [MockSensor() for _ in range(count)]

    def get_data(
        self,
        callback: Callable[[MacAndSensorData], None],
        macs: List[str] = [],
        run_flag: RunFlag = RunFlag(),
        bt_device: str = None,
    ):
        while True:
            for sensor in self.sensors:
                reading = sensor.get_reading()
                if reading:
                    callback(reading)
            time.sleep(1)
