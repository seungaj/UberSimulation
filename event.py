"""Simulation Events

This file should contain all of the classes necessary to model the different
kinds of events in the simulation.
"""
from __future__ import annotations
from typing import List
from rider import Rider, WAITING, CANCELLED, SATISFIED
from dispatcher import Dispatcher
from driver import Driver
from location import deserialize_location
from monitor import Monitor, RIDER, DRIVER, REQUEST, CANCEL, PICKUP, DROPOFF


class Event:
    """An event.

    Events have an ordering that is based on the event timestamp: Events with
    older timestamps are less than those with newer timestamps.

    This class is abstract; subclasses must implement do().

    You may, if you wish, change the API of this class to add
    extra public methods or attributes. Make sure that anything
    you add makes sense for ALL events, and not just a particular
    event type.

    Document any such changes carefully!

    === Attributes ===
    timestamp: A timestamp for this event.
    """

    timestamp: int

    def __init__(self, timestamp: int) -> None:
        """Initialize an Event with a given timestamp.

        Precondition: timestamp must be a non-negative integer.

        >>> Event(7).timestamp
        7
        """
        self.timestamp = timestamp

    # The following six 'magic methods' are overridden to allow for easy
    # comparison of Event instances. All comparisons simply perform the
    # same comparison on the 'timestamp' attribute of the two events.
    def __eq__(self, other: Event) -> bool:
        """Return True iff this Event is equal to <other>.

        Two events are equal iff they have the same timestamp.

        >>> first = Event(1)
        >>> second = Event(2)
        >>> first == second
        False
        >>> second.timestamp = first.timestamp
        >>> first == second
        True
        """
        return self.timestamp == other.timestamp

    def __ne__(self, other: Event) -> bool:
        """Return True iff this Event is not equal to <other>.

        >>> first = Event(1)
        >>> second = Event(2)
        >>> first != second
        True
        >>> second.timestamp = first.timestamp
        >>> first != second
        False
        """
        return not self == other

    def __lt__(self, other: Event) -> bool:
        """Return True iff this Event is less than <other>.

        >>> first = Event(1)
        >>> second = Event(2)
        >>> first < second
        True
        >>> second < first
        False
        """
        return self.timestamp < other.timestamp

    def __le__(self, other: Event) -> bool:
        """Return True iff this Event is less than or equal to <other>.

        >>> first = Event(1)
        >>> second = Event(2)
        >>> first <= first
        True
        >>> first <= second
        True
        >>> second <= first
        False
        """
        return self.timestamp <= other.timestamp

    def __gt__(self, other: Event) -> bool:
        """Return True iff this Event is greater than <other>.

        >>> first = Event(1)
        >>> second = Event(2)
        >>> first > second
        False
        >>> second > first
        True
        """
        return not self <= other

    def __ge__(self, other: Event) -> bool:
        """Return True iff this Event is greater than or equal to <other>.

        >>> first = Event(1)
        >>> second = Event(2)
        >>> first >= first
        True
        >>> first >= second
        False
        >>> second >= first
        True
        """
        return not self < other

    def __str__(self) -> str:
        """Return a string representation of this event.

        """
        raise NotImplementedError("Implemented in a subclass")

    def do(self, dispatcher: Dispatcher, monitor: Monitor) -> List[Event]:
        """Do this Event.

        Update the state of the simulation, using the dispatcher, and any
        attributes according to the meaning of the event.

        Notify the monitor of any activities that have occurred during the
        event.

        Return a list of new events spawned by this event (making sure the
        timestamps are correct).

        Note: the "business logic" of what actually happens should not be
        handled in any Event classes.

        """
        raise NotImplementedError("Implemented in a subclass")


class RiderRequest(Event):
    """A rider requests a driver.

    === Attributes ===
    rider: The rider.
    """

    rider: Rider

    def __init__(self, timestamp: int, rider: Rider) -> None:
        """Initialize a RiderRequest event.

        """
        super().__init__(timestamp)
        self.rider = rider

    def do(self, dispatcher: Dispatcher, monitor: Monitor) -> List[Event]:
        """Assign the rider to a driver or add the rider to a waiting list.
        If the rider is assigned to a driver, the driver starts driving to
        the rider.

        Return a Cancellation event. If the rider is assigned to a driver,
        also return a Pickup event.

        """
        monitor.notify(self.timestamp, RIDER, REQUEST,
                       self.rider.id, self.rider.origin)

        events = []
        driver = dispatcher.request_driver(self.rider)
        if driver is not None:
            travel_time = driver.start_drive(self.rider.origin)
            events.append(Pickup(self.timestamp + travel_time,
                                 self.rider, driver))
        events.append(Cancellation(self.timestamp + self.rider.patience,
                                   self.rider))
        return events

    def __str__(self) -> str:
        """Return a string representation of this event.

        """
        return "{} -- {}: Request a driver".format(self.timestamp, self.rider)


class DriverRequest(Event):
    """A driver requests a rider.

    === Attributes ===
    driver: The driver.
    """

    driver: Driver

    def __init__(self, timestamp: int, driver: Driver) -> None:
        """Initialize a DriverRequest event.

        """
        super().__init__(timestamp)
        self.driver = driver

    def do(self, dispatcher: Dispatcher, monitor: Monitor) -> List[Event]:
        """Register the driver, if this is the first request, and
        assign a rider to the driver, if one is available.

        If a rider is available, return a Pickup event.

        """
        # Notify the monitor about the request.

        # Request a rider from the dispatcher.
        # If there is one available, the driver starts driving towards the
        # rider, and the method returns a Pickup event for when the driver
        # arrives at the riders location.
        monitor.notify(self.timestamp, DRIVER, REQUEST,
                       self.driver.id, self.driver.location)

        events = []
        rider = dispatcher.request_rider(self.driver)

        if rider is not None:
            travel_time = self.driver.start_drive(rider.origin)
            events.append(Pickup(self.timestamp + travel_time,
                                 rider, self.driver))

        return events

    def __str__(self) -> str:
        """Return a string representation of this event.

        """
        return "{} -- {}: Request a rider".format(self.timestamp, self.driver)


class Cancellation(Event):
    """A rider cancels a ride.

    === Attributes ===
    rider: The Rider.
    """

    rider: Rider

    def __init__(self, timestamp: int, rider: Rider) -> None:
        """Initialize a Cancellation event.

        """
        super().__init__(timestamp)
        self.rider = rider

    def __str__(self) -> str:
        """Return a string representation.

        """
        return "Cancellation Id: ({}, Timestamp: {})".format(
            self.rider.id, self.timestamp)

    def do(self, dispatcher: Dispatcher, monitor: Monitor) -> List[Event]:
        """Cancel the ride if rider's status is waiting but there are
        no available drivers.

        """
        events = []
        driver = dispatcher.request_driver(self.rider)
        if self.rider.status == WAITING and dispatcher.available_d != []:
            if driver is not None:
                dispatcher.available_d.remove(driver)
                dispatcher.cancel_ride(self.rider)
                self.rider.status = CANCELLED
                driver.end_ride()
                driver.end_drive()
                driver.location = self.rider.origin
                monitor.notify(self.timestamp, RIDER, CANCEL, self.rider.id,
                               self.rider.origin)
                monitor.notify(self.timestamp, DRIVER, CANCEL, driver.id,
                               driver.location)
                events.append(DriverRequest(self.timestamp, driver))
        return events


class Pickup(Event):
    """A driver picks up a rider.

    === Attributes ===
    driver: The driver.
    rider: The rider
    """

    rider: Rider
    driver: Driver

    def __init__(self, timestamp: int, rider: Rider, driver: Driver) -> None:
        """Initialize a Pickup event.

        """
        super().__init__(timestamp)
        self.rider = rider
        self.driver = driver

    def __str__(self) -> str:
        """Return a string representation.

        """
        return "Pickup Timestamp: ({}, Rider: {}, Driver:{})".format(
            self.timestamp, self.rider.id, self.driver.id)

    def do(self, dispatcher: Dispatcher, monitor: Monitor) -> List[Event]:
        """Pickup the rider if rider's patience is greater than rider's
        waiting time and driver is available and is waiting.

        """
        events = []

        if self.rider.status == WAITING and dispatcher.available_d != []:
            dispatcher.available_d.remove(self.driver)

            self.rider.status = SATISFIED
            self.driver.is_idle = False
            monitor.notify(self.timestamp, RIDER, PICKUP, self.rider.id,
                           self.rider.origin)
            monitor.notify(self.timestamp, DRIVER, PICKUP, self.driver.id,
                           self.driver.location)
            events.append(Dropoff(self.timestamp, self.rider, self.driver))
            self.driver.location = self.rider.origin
            self.driver.destination = self.rider.destination
        return events


class Dropoff(Event):
    """A driver drops off a rider.

    === Attributes ===
    driver: The driver
    rider: The rider
    """

    rider: Rider
    driver: Driver

    def __init__(self, timestamp: int, rider: Rider, driver: Driver) -> None:
        """Initialize a Dropoff event.

        """
        super().__init__(timestamp)
        self.driver = driver
        self.rider = rider

    def __str__(self) -> str:
        """Return a string representation.

        """
        return "Dropoff Timestamp: ({}, Rider: {}, Driver:{})".format(
            self.timestamp, self.rider.id, self.driver.id)

    def do(self, dispatcher: Dispatcher, monitor: Monitor) -> List[Event]:
        """Pickup the rider if rider's status is satisfied.

        """
        events = []
        if self.rider.status == SATISFIED:
            dispatcher.available_d.append(self.driver)
            self.driver.end_ride()
            monitor.notify(self.timestamp, DRIVER, DROPOFF, self.driver.id,
                           self.driver.location)
            monitor.notify(self.timestamp, RIDER, DROPOFF, self.rider.id,
                           self.rider.destination)
            events.append(DriverRequest(self.timestamp, self.driver))

        return events


def create_event_list(filename: str) -> List[Event]:
    """Return a list of Events based on raw list of events in <filename>.

    Precondition: the file stored at <filename> is in the format specified
    by the assignment handout.

    filename: The name of a file that contains the list of events.
    """
    events = []
    with open(filename, "r") as file:
        for line in file:
            line = line.strip()

            if not line or line.startswith("#"):
                # Skip lines that are blank or start with #.
                continue

            # Create a list of words in the line, e.g.
            # ['10', 'RiderRequest', 'Cerise', '4,2', '1,5', '15'].
            # Note that these are strings, and you'll need to convert some
            # of them to a different type.
            tokens = line.split()
            timestamp = int(tokens[0])
            event_type = tokens[1]

            # HINT: Use Location.deserialize to convert the location string to
            # a location.

            if event_type == "DriverRequest":
                # Create a DriverRequest event.
                location = deserialize_location(tokens[3])
                speed = int(tokens[-1])
                identifier = tokens[2]
                driver = Driver(identifier, location, speed)
                events.append(DriverRequest(timestamp, driver))
            elif event_type == "RiderRequest":
                # Create a RiderRequest event.
                identifier = tokens[2]
                origin = deserialize_location(tokens[3])
                destination = deserialize_location(tokens[4])
                patience = int(tokens[-1])
                rider = Rider(identifier, patience, origin, destination)
                events.append(RiderRequest(timestamp, rider))

    return events


if __name__ == '__main__':
    import python_ta
    python_ta.check_all(
        config={
            'allowed-io': ['create_event_list'],
            'extra-imports': ['rider', 'dispatcher', 'driver',
                              'location', 'monitor']})
