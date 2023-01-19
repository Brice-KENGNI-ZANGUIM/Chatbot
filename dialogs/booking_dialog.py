# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""Flight booking dialog."""

import requests
from datetime import datetime
from datatypes_date_time.timex import Timex
from botbuilder.dialogs import WaterfallDialog, WaterfallStepContext, DialogTurnResult
from botbuilder.dialogs.prompts import ConfirmPrompt, TextPrompt, PromptOptions
from botbuilder.core import MessageFactory, CardFactory, BotTelemetryClient, NullTelemetryClient
from botbuilder.schema import Attachment, InputHints, HeroCard, CardAction, CardImage
from .cancel_and_help_dialog import CancelAndHelpDialog
from .destination_resolver_dialog import DestinationResolverDialog
from .origin_resolver_dialog import OriginResolverDialog
from .date_resolver_dialog import DateResolverDialog
from .return_resolver_dialog import ReturnResolverDialog
from .budget_resolver_dialog import BudgetResolverDialog
from booking_details import BookingDetails
from .resources.flight_card import FLIGHT_CARD_CONTENT
from flight_booking_recognizer import FlightBookingRecognizer
from conversation_records import ConversationRecords
from config import DefaultConfig
import logging
from opencensus.ext.azure.log_exporter import AzureLogHandler


class BookingDialog(CancelAndHelpDialog):
    """Flight booking implementation."""

    def __init__(
        self,
        luis_recognizer: FlightBookingRecognizer,
        dialog_id: str = None,
        telemetry_client: BotTelemetryClient = NullTelemetryClient(),
        conversation_records: ConversationRecords = ConversationRecords()
    ):
        super(BookingDialog, self).__init__(
            luis_recognizer=luis_recognizer,
            dialog_id=(dialog_id or BookingDialog.__name__),
            telemetry_client=telemetry_client,
            conversation_records=conversation_records
        )
        self.telemetry_client = telemetry_client
        text_prompt = TextPrompt(TextPrompt.__name__)
        text_prompt.telemetry_client = telemetry_client

        self.conf = DefaultConfig()
        self.logger = logging.getLogger(__name__)
        self.logger.addHandler(AzureLogHandler(
            connection_string=f'InstrumentationKey={self.conf.APPINSIGHTS_INSTRUMENTATION_KEY}')
        )

        self.FAILED = "booking_failed"

        waterfall_dialog = WaterfallDialog(
            WaterfallDialog.__name__,
            [
                self.destination_step,
                self.origin_step,
                self.travel_date_step,
                self.return_date_step,
                self.budget_step,
                self.confirm_step,
                self.final_step,
            ],
        )
        waterfall_dialog.telemetry_client = telemetry_client

        self.add_dialog(text_prompt)
        self.add_dialog(ConfirmPrompt(ConfirmPrompt.__name__))
        self.add_dialog(
            DestinationResolverDialog(
                self._luis_recognizer,
                DestinationResolverDialog.__name__,
                self.telemetry_client,
                self.conversation_records
            )
        )
        self.add_dialog(
            OriginResolverDialog(
                self._luis_recognizer,
                OriginResolverDialog.__name__,
                self.telemetry_client,
                self.conversation_records
            )
        )
        self.add_dialog(
            DateResolverDialog(
                DateResolverDialog.__name__,
                self.telemetry_client,
                self.conversation_records
            )
        )
        self.add_dialog(
            ReturnResolverDialog(
                ReturnResolverDialog.__name__,
                self.telemetry_client,
                self.conversation_records
            )
        )
        self.add_dialog(
            BudgetResolverDialog(
                BudgetResolverDialog.__name__,
                self.telemetry_client,
                self.conversation_records
            )
        )
        self.add_dialog(waterfall_dialog)

        self.initial_dialog_id = WaterfallDialog.__name__


    async def destination_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Prompt for destination."""
        booking_details = step_context.options        
        if booking_details.destination is None:
            return await step_context.begin_dialog(
                DestinationResolverDialog.__name__, booking_details.destination
            )
        return await step_context.next(booking_details.destination)


    async def origin_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Prompt for origin city."""
        booking_details = step_context.options
        booking_details.destination = step_context.result
        if booking_details.origin is None:
            return await step_context.begin_dialog(
                OriginResolverDialog.__name__, booking_details.origin
            )
        return await step_context.next(booking_details.origin)


    async def travel_date_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Prompt for travel date.
        This will use the DATE_RESOLVER_DIALOG."""
        booking_details = step_context.options
        booking_details.origin = step_context.result
        if not booking_details.travel_date or self.is_ambiguous(booking_details.travel_date):
            return await step_context.begin_dialog(
                DateResolverDialog.__name__, booking_details.travel_date
            )
        return await step_context.next(booking_details.travel_date)


    async def return_date_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Prompt for travel date.
        This will use the DATE_RESOLVER_DIALOG."""
        booking_details = step_context.options
        booking_details.travel_date = step_context.result
        # If the return date is inferior to the travel date, we erase both and start over
        if booking_details.travel_date < datetime.today().strftime("%Y-%m-%d"):
            booking_details.travel_date = None
            msg_text = ("Hmm, a trip in the past... Not a bad idea, but let's save it for another time!")
            message = MessageFactory.text(msg_text, msg_text, InputHints.ignoring_input)
            self.conversation_records.add_turn(msg_text)
            await step_context.context.send_activity(message)
            return await step_context.replace_dialog(self.id, booking_details)
        if not booking_details.return_date or self.is_ambiguous(booking_details.return_date):
            return await step_context.begin_dialog(
                ReturnResolverDialog.__name__, booking_details.return_date
            )
        return await step_context.next(booking_details.return_date)


    async def budget_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Prompt for origin city."""
        booking_details = step_context.options
        booking_details.return_date = step_context.result
        # If the return date is inferior to the travel date, we erase both and start over
        if booking_details.travel_date > booking_details.return_date:
            booking_details.travel_date = None
            booking_details.return_date = None
            msg_text = ("Your return date can't be prior to the travel date. Please input again your dates.")
            message = MessageFactory.text(msg_text, msg_text, InputHints.ignoring_input)
            self.conversation_records.add_turn(msg_text)
            await step_context.context.send_activity(message)
            return await step_context.replace_dialog(self.id, booking_details)
        # Otherwise, let's proceed to budget capture through a dedicated dialog
        if booking_details.budget is None:
            return await step_context.begin_dialog(
                BudgetResolverDialog.__name__, booking_details.amount
            )
        return await step_context.next(booking_details.amount)


    async def confirm_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Offer a flight proposal to the user and ask for confirmation"""
        booking_details = step_context.options
        booking_details.budget = '$' + str(step_context.result)
        booking_details.amount = int(step_context.result)
        confirmation = MessageFactory.list([])
        user_name = step_context._turn_context.activity.from_property.name
        user_id = step_context._turn_context.activity.from_property.id
        try:
            card = self.create_reservation_card(booking_details, user_name, user_id)
            if card is not None:
                step_context.values[self.FAILED] = False
                confirmation.attachments.append(card)
                await step_context.context.send_activity(confirmation)
                msg = "Is this trip OK for you?"
                img = 'ok'
            else:
                step_context.values[self.FAILED] = True
                msg = "No result found. Would you like to retry?"
                img = 'restart'
            
            self.conversation_records.add_turn(msg)
            confirm_card = self.create_confirm_card(msg, img)
            attach_list = MessageFactory.list([])
            attach_list.attachments.append(confirm_card)
            await step_context.context.send_activity(attach_list)
            waiting_msg = "Waiting for your input..."
            prompt_message = MessageFactory.text(waiting_msg, waiting_msg, InputHints.expecting_input)
            return await step_context.prompt(
                TextPrompt.__name__, PromptOptions(prompt=prompt_message)
            )

        except Exception as ex:
            try:
                self.logger.info(f"Exception: {ex.message}")
            except Exception as excep:
                self.logger.info(f"Exception: {ex}")
                pass
            finally:
                step_context.values[self.FAILED] = True
                msg = "No result found. Would you like to retry?"
                self.conversation_records.add_turn(msg)
                confirm_card = self.create_confirm_card(msg, 'restart')
                attach_list = MessageFactory.list([])
                attach_list.attachments.append(confirm_card)
                await step_context.context.send_activity(attach_list)
                waiting_msg = "Waiting for your input..."
                prompt_message = MessageFactory.text(
                    waiting_msg, waiting_msg, InputHints.expecting_input
                )
                return await step_context.prompt(
                    TextPrompt.__name__, PromptOptions(prompt=prompt_message)
                )
                


    async def final_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Complete the interaction and end the dialog."""
        print("in the final step")
        booking_details = step_context.options
        self.conversation_records.add_turn(step_context.result, False)
        if step_context.result == "booking_action_pos":
            if step_context.values[self.FAILED]:
                msg_text = "Let's start over then."
                self.conversation_records.add_turn(msg_text)
                message = MessageFactory.text(
                    msg_text, msg_text, InputHints.ignoring_input
                )
                await step_context.context.send_activity(message)
                return await step_context.replace_dialog(self.id, BookingDetails())
            else:
                booking_details.booked = True
        else:
            if not step_context.values[self.FAILED]:
                msg_text = "I'm sorry, let's start over."
                self.conversation_records.add_turn(msg_text)
                message = MessageFactory.text(
                    msg_text, msg_text, InputHints.ignoring_input
                )
                await step_context.context.send_activity(message)
                return await step_context.replace_dialog(self.id, BookingDetails())
        return await step_context.end_dialog(booking_details)
        

    def is_ambiguous(self, timex: str) -> bool:
        """Ensure time is correct."""
        timex_property = Timex(timex)
        return "definite" not in timex_property.types


    def filled_up_to(self, step: str, booking_details) -> bool:
        """Ensure the booking_details object contains no None attribute up to a certain point"""
        attr = ['destination', 'origin', 'travel_date', 'return_date', 'budget', 'stop']
        i = 0
        filled = True
        while attr[i] != step:
            if getattr(booking_details, attr[i]) == None:
                filled = False
            i += 1
        return filled


    def create_reservation_card(self, booking, user_name, user_id) -> Attachment:
        flight = self.make_reservation(booking)
        if len(flight) > 0 :
            FLIGHT_CARD_CONTENT['body'][1]['text'] = user_name
            FLIGHT_CARD_CONTENT['body'][2]['text'] = user_id
            FLIGHT_CARD_CONTENT['body'][3]['text'] = f"{flight['go_dep_date']} -> {flight['go_arr_date']}"
            FLIGHT_CARD_CONTENT['body'][6]['text'] = f"{flight['re_dep_date']} -> {flight['re_arr_date']}"
            FLIGHT_CARD_CONTENT['body'][10]['columns'][1]['items'][0]['text'] = '$' + str(flight['price'])
            FLIGHT_CARD_CONTENT['body'][5]['columns'][0]['items'][0]['text'] = flight['go_dep_airport_code']
            FLIGHT_CARD_CONTENT['body'][8]['columns'][2]['items'][0]['text'] = flight['re_arr_airport_code']
            FLIGHT_CARD_CONTENT['body'][4]['columns'][0]['items'][0]['text'] = flight['go_dep_airport_name']
            FLIGHT_CARD_CONTENT['body'][7]['columns'][1]['items'][0]['text'] = flight['re_arr_airport_name']
            FLIGHT_CARD_CONTENT['body'][4]['columns'][0]['items'][1]['text'] = f"{flight['dep_city_name']}, {flight['dep_country_name']}"
            FLIGHT_CARD_CONTENT['body'][7]['columns'][1]['items'][1]['text'] = f"{flight['dep_city_name']}, {flight['dep_country_name']}"
            FLIGHT_CARD_CONTENT['body'][5]['columns'][2]['items'][0]['text'] = flight['go_arr_airport_code']
            FLIGHT_CARD_CONTENT['body'][8]['columns'][0]['items'][0]['text'] = flight['re_dep_airport_code']
            FLIGHT_CARD_CONTENT['body'][4]['columns'][1]['items'][0]['text'] = flight['go_arr_airport_name']
            FLIGHT_CARD_CONTENT['body'][7]['columns'][0]['items'][0]['text'] = flight['re_dep_airport_name']
            FLIGHT_CARD_CONTENT['body'][4]['columns'][1]['items'][1]['text'] = f"{flight['arr_city_name']}, {flight['arr_country_name']}"
            FLIGHT_CARD_CONTENT['body'][7]['columns'][0]['items'][1]['text'] = f"{flight['arr_city_name']}, {flight['arr_country_name']}"
            return CardFactory.adaptive_card(FLIGHT_CARD_CONTENT)
        else:
            return None


    def make_reservation(self, booking):
        """Create an adaptive card."""
        origin_city = self.get_city(booking.origin)
        destination_city = self.get_city(booking.destination)
        if (origin_city['country_name'] != "Some country") and (destination_city['country_name'] != "Some country"):
            go_date = datetime.strptime(booking.travel_date, '%Y-%m-%d').strftime('%d/%m/%Y')
            re_date = datetime.strptime(booking.return_date, '%Y-%m-%d').strftime('%d/%m/%Y')
            max_price = booking.amount
            flight = self.get_flight(
                go_date, re_date, origin_city['city_code'], destination_city['city_code'], max_price
            )
            if len(flight) > 0:
                go_origin_airport = self.get_airport_name(flight['go_dep_airport_code'])
                go_destination_airport = self.get_airport_name(flight['go_arr_airport_code'])
                re_origin_airport = go_destination_airport if flight['re_dep_airport_code'] == flight['go_arr_airport_code'] else self.get_airport_name(flight['re_dep_airport_code'])
                re_destination_airport = go_origin_airport if flight['re_arr_airport_code'] == flight['go_dep_airport_code'] else self.get_airport_name(flight['re_arr_airport_code'])
                flight['go_dep_airport_name'] = booking.origin if go_origin_airport == "" else go_origin_airport
                flight['go_arr_airport_name'] = booking.destination if go_destination_airport == "" else go_destination_airport
                flight['re_dep_airport_name'] = booking.destination if re_origin_airport == "" else re_origin_airport
                flight['re_arr_airport_name'] = booking.origin if re_destination_airport == "" else re_destination_airport
                flight['dep_country_name'] = origin_city['country_name']
                flight['arr_country_name'] = destination_city['country_name']
                flight['dep_city_name'] = origin_city['city_name']
                flight['arr_city_name'] = destination_city['city_name']
                return flight
        flight = {}
        return flight


    def get_city(self, location_name):
        headers = {'apikey': self.conf.TEQUILA_KIWI_API_KEY , 'accept': 'application/json'}
        url = f'https://api.tequila.kiwi.com/locations/query?term={location_name}&location_types=city&limit=1&active_only=true'
        response = requests.get(url=url, headers=headers)
        if response.status_code == 200:
            json = response.json()
            if len(json['locations']) > 0:
                res = {
                    "country_name": json['locations'][0]['country']['name'],
                    "city_name": json['locations'][0]['name'],
                    "city_code": json['locations'][0]['code']
                }
                return res
        res = {
            "country_name": "Some country",
            "airport_name": location_name,
            "iata_code": location_name[:3].upper()
        }
        return res

    
    def get_airport_name(self, airport_code):
        headers = {'apikey': self.conf.TEQUILA_KIWI_API_KEY , 'accept': 'application/json'}
        url = f'https://api.tequila.kiwi.com/locations/query?term={airport_code}&location_types=airport&limit=1&active_only=true'
        response = requests.get(url=url, headers=headers)
        if response.status_code == 200:
            json = response.json()
            if len(json['locations']) > 0:
                return json['locations'][0]['name']
        return ""

    
    def get_flight(self, go_date, re_date, dep_city_code, arr_city_code, budget):
        headers = {'apikey': self.conf.TEQUILA_KIWI_API_KEY , 'accept': 'application/json'}
        url = f"https://api.tequila.kiwi.com/v2/search?fly_from={dep_city_code}&fly_to={arr_city_code}&date_from={go_date}&date_to={go_date}&return_from={re_date}&return_to={re_date}&curr=USD&price_to={budget}&limit=1"
        response = requests.get(url=url, headers=headers)
        if response.status_code == 200:
            json = response.json()
            if len(json['data']) > 0:
                res = {
                    "price": json['data'][0]['price']
                }
                for i in range(len(json['data'][0]['route'])):
                    if json['data'][0]['route'][i]['cityCodeFrom'] == dep_city_code:
                        res["go_dep_airport_code"] = json['data'][0]['route'][i]['flyFrom']
                        res['go_dep_date'] = datetime.strptime(
                            json['data'][0]['route'][i]['local_departure'], "%Y-%m-%dT%H:%M:%S.000Z"
                        ).strftime('%a %d %B %Y, %Hh%M')
                    if json['data'][0]['route'][i]['cityCodeFrom'] == arr_city_code:
                        res["re_dep_airport_code"] = json['data'][0]['route'][i]['flyFrom']
                        res['re_dep_date'] = datetime.strptime(
                            json['data'][0]['route'][i]['local_departure'], "%Y-%m-%dT%H:%M:%S.000Z"
                        ).strftime('%a %d %B %Y, %Hh%M')
                    if json['data'][0]['route'][i]['cityCodeTo'] == dep_city_code:
                        res["re_arr_airport_code"] = json['data'][0]['route'][i]['flyTo']
                        res['re_arr_date'] = datetime.strptime(
                            json['data'][0]['route'][i]['local_arrival'], "%Y-%m-%dT%H:%M:%S.000Z"
                        ).strftime('%a %d %B %Y, %Hh%M')
                    if json['data'][0]['route'][i]['cityCodeTo'] == arr_city_code:
                        res["go_arr_airport_code"] = json['data'][0]['route'][i]['flyTo']
                        res['go_arr_date'] = datetime.strptime(
                            json['data'][0]['route'][i]['local_arrival'], "%Y-%m-%dT%H:%M:%S.000Z"
                        ).strftime('%a %d %B %Y, %Hh%M')
                return res
        res = {}
        return res


    def create_confirm_card(self, title, image) -> Attachment:
        if image == 'ok':
            url = "https://findicons.com/files/icons/1014/ivista/32/good_or_tick.png"
        else:
            url = "https://findicons.com/files/icons/2796/metro_uinvert_dock/32/power_restart.png"
        card = HeroCard(
            title=title,
            #images=[
            #    CardImage(
            #        url=url
            #    )
            #],
            buttons=[
                CardAction(
                    type="messageBack",
                    title="Yes",
                    value="booking_action_pos",
                    text="booking_action_pos"
                ),
                CardAction(
                    type="messageBack",
                    title="No",
                    value="booking_action_neg",
                    text="booking_action_neg"
                )
            ],
        )
        return CardFactory.hero_card(card)
