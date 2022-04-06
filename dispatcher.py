"""Dispatcher for the simulation"""

from typing import Optional
from driver import Driver
from rider import Rider


class Dispatcher:
    """A dispatcher fulfills requests from riders and drivers for a
    ride-sharing service.

    When a rider requests a driver, the dispatcher assigns a driver to the
    rider. If no driver is available, the rider is placed on a waiting
    list for the next available driver. A rider that has not yet been
    picked up by a driver may cancel their request.

    When a driver requests a rider, the dispatcher assigns a rider from
    the waiting list to the driver. If there is no rider on the waiting list
    the dispatcher does nothing. Once a driver requests a rider, the driver
    is registered with the dispatcher, and will be used to fulfill future
    rider requests.
    """

    available_d: list
    waiting_r: list

    def __init__(self) -> None:
        """Initialize a Dispatcher.

        """
        self.available_d = []
        self.waiting_r = []

    def __str__(self) -> str:
        """Return a string representation.

        """
        return "Dispatch ({} drivers, {} riders)".format(
            len(self.available_d), len(self.waiting_r))

    def request_driver(self, rider: Rider) -> Optional[Driver]:
        """Return a driver for the rider, or None if no driver is available.

        Add the rider to the waiting list if there is no available driver.

        """

        if not self.available_d:
            self.waiting_r.append(rider)
            return None
        if len(self.available_d) == 1:
            self.available_d[0].is_idle = False
            return self.available_d[0]

        i = 0
        nearest = self.available_d[0]
        while i < len(self.available_d):
            if nearest.start_drive(rider.origin) > \
               (self.available_d[i].start_drive(rider.origin)):
                nearest = self.available_d[i]
            i += 1
        nearest.is_idle = False
        return nearest

    def request_rider(self, driver: Driver) -> Optional[Rider]:
        """Return a rider for the driver, or None if no rider is available.

        If this is a new driver, register the driver for future rider requests.

        """

        if driver not in self.available_d:
            self.available_d.append(driver)
        elif len(self.waiting_r) > 0:
            driver.is_idle = False
            nearest = self.waiting_r.pop(0)
            return nearest
        return None

    def cancel_ride(self, rider: Rider) -> None:
        """Cancel the ride for rider.

        """
        if rider in self.waiting_r:
            self.waiting_r.remove(rider)


if __name__ == '__main__':
    import python_ta
    python_ta.check_all(config={'extra-imports': ['typing', 'driver', 'rider']})
