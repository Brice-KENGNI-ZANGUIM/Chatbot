# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.


class BookingDetails:
    def __init__(
        self,
        destination: str = None,
        origin: str = None,
        travel_date: str = None,
        return_date:str = None,
        budget: str = None,
        amount: int = None,
        unsupported_airports = None,
        text: str = None
    ):
        if unsupported_airports is None:
            unsupported_airports = []
        self.destination = destination
        self.origin = origin
        self.travel_date = travel_date
        self.return_date = return_date
        self.budget = budget
        self.amount = amount
        self.unsupported_airports = unsupported_airports
        self.text = text
        self.booked = False
