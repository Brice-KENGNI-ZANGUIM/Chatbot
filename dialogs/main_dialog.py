# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from botbuilder.dialogs import (
    ComponentDialog,
    WaterfallDialog,
    WaterfallStepContext,
    DialogTurnResult,
)
from botbuilder.dialogs.prompts import TextPrompt, PromptOptions, ConfirmPrompt
from botbuilder.core import (
    MessageFactory,
    TurnContext,
    BotTelemetryClient,
    NullTelemetryClient,
    CardFactory
)
from botbuilder.schema import InputHints, Attachment, HeroCard, CardAction, CardImage

from booking_details import BookingDetails
from conversation_records import ConversationRecords
from flight_booking_recognizer import FlightBookingRecognizer
from helpers.luis_helper import LuisHelper, Intent
from .booking_dialog import BookingDialog
from config import DefaultConfig
import logging
from opencensus.ext.azure.log_exporter import AzureLogHandler


class MainDialog(ComponentDialog):
    def __init__(
        self,
        luis_recognizer: FlightBookingRecognizer,
        booking_dialog: BookingDialog,
        telemetry_client: BotTelemetryClient = None,
    ):
        super(MainDialog, self).__init__(MainDialog.__name__)
        self.telemetry_client = telemetry_client or NullTelemetryClient()
        self.conversation_records = ConversationRecords()

        text_prompt = TextPrompt(TextPrompt.__name__)
        text_prompt.telemetry_client = self.telemetry_client

        booking_dialog = BookingDialog(
            luis_recognizer=luis_recognizer,
            telemetry_client=telemetry_client,
            conversation_records=self.conversation_records
        )
        booking_dialog.telemetry_client = self.telemetry_client
        booking_dialog.conversation_records = self.conversation_records

        conf = DefaultConfig()
        self.logger = logging.getLogger(__name__)
        self.logger.addHandler(AzureLogHandler(
            connection_string=f'InstrumentationKey={conf.APPINSIGHTS_INSTRUMENTATION_KEY}')
        )

        wf_dialog = WaterfallDialog(
            "WFDialog", [self.act_step, self.survey_step, self.final_step]
        )
        wf_dialog.telemetry_client = self.telemetry_client

        self._luis_recognizer = luis_recognizer
        self._booking_dialog_id = booking_dialog.id

        self.add_dialog(text_prompt)
        self.add_dialog(ConfirmPrompt(ConfirmPrompt.__name__))
        self.add_dialog(booking_dialog)
        self.add_dialog(wf_dialog)

        self.initial_dialog_id = "WFDialog"


    async def intro_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        if not self._luis_recognizer.is_configured:
            await step_context.context.send_activity(
                MessageFactory.text(
                    "NOTE: LUIS is not configured. To enable all capabilities, add 'LuisAppId', 'LuisAPIKey' and "
                    "'LuisAPIHostName' to the appsettings.json file.",
                    input_hint=InputHints.ignoring_input,
                )
            )

            return await step_context.next(None)
        message_text = "What can I help you with today?"
        prompt_message = MessageFactory.text(
            message_text, message_text, InputHints.expecting_input
        )

        return await step_context.prompt(
            TextPrompt.__name__, PromptOptions(prompt=prompt_message)
        )


    async def act_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        self.conversation_records.reset()
        self.conversation_records.add_turn("What can I help you with today?")

        if not self._luis_recognizer.is_configured:
            # LUIS is not configured, we just run the BookingDialog path with an empty BookingDetailsInstance.
            return await step_context.begin_dialog(
                self._booking_dialog_id, BookingDetails()
            )

        # Call LUIS and gather any potential booking details. (Note the TurnContext has the response to the prompt.)
        intent, luis_result = await LuisHelper.execute_luis_query(
            self._luis_recognizer, step_context.context
        )
        self.conversation_records.add_turn(luis_result.text, False)

        if intent == Intent.BOOK_FLIGHT.value and luis_result:
            # Show a warning for Origin and Destination if we can't resolve them.
            await MainDialog._show_warning_for_unsupported_cities(
                step_context.context, luis_result
            )

            # Run the BookingDialog giving it whatever details we have from the LUIS call.
            return await step_context.begin_dialog(self._booking_dialog_id, luis_result)

        if (intent == Intent.CANCEL.value) or (intent == Intent.STOP.value):
            self.conversation_records.add_turn("Cancelling")
            await step_context.context.send_activity("Cancelling")

        else:
            didnt_understand_text = (
                "Sorry, I didn't get that. Please try asking in a different way"
            )
            self.conversation_records.add_turn(didnt_understand_text)
            didnt_understand_message = MessageFactory.text(
                didnt_understand_text, didnt_understand_text, InputHints.ignoring_input
            )
            await step_context.context.send_activity(didnt_understand_message)

        return await step_context.next(None)

    
    async def survey_step(self, step_context: WaterfallStepContext):
        """
        Creates and sends an activity with suggested actions to the user. When the user
        clicks one of the buttons the text value from the "CardAction" will be displayed
        in the channel just as if the user entered the text. There are multiple
        "ActionTypes" that may be used for different situations.
        """
        # If the child dialog ("BookingDialog") was cancelled or the user failed to confirm,
        # the Result here will be null.
        if step_context.result is not None:
            if step_context.result.booked:
                self.conversation_records.add_turn("Yes", False)
                msg_txt = "The booking has been placed. You're good to go!"
                self.conversation_records.add_turn(msg_txt)
                message = MessageFactory.text(msg_txt, msg_txt, InputHints.ignoring_input)
                await step_context.context.send_activity(message)

        msg = "Are you satisfied with the service I provided?"
        self.conversation_records.add_turn(msg)
        confirm_card = self.create_confirm_card(msg)
        confirmation = MessageFactory.list([])
        confirmation.attachments.append(confirm_card)
        await step_context.context.send_activity(confirmation)
        waiting_msg = "Waiting for your input..."
        prompt_message = MessageFactory.text(
            waiting_msg, waiting_msg, InputHints.expecting_input
        )
        return await step_context.prompt(
            TextPrompt.__name__, PromptOptions(prompt=prompt_message)
        )
    
    
    async def final_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:        
        if step_context.result is not None:

            if step_context.result == "booking_action_neg":
                self.conversation_records.add_turn("No", False)
                message = MessageFactory.text(
                    "I'm sorry to hear that! Rest assured we'll do all we can to improve our quality of service based on your feedback.",
                    InputHints.ignoring_input
                )
                self.logger.warning(f"Service_attempt_failed :: {str(self.conversation_records.conversation_scripts)}")
            else:
                self.conversation_records.add_turn("Yes", False)
                message = MessageFactory.text(
                    "Glad to hear it, your feedback is essential to improve our quality of service.",
                    InputHints.ignoring_input
                )
                self.logger.info(f"Service_attempt_succeeded :: {str(self.conversation_records.conversation_scripts)}")
            await step_context.context.send_activity(message)

        message = MessageFactory.text("Have a good day", InputHints.ignoring_input)
        await step_context.context.send_activity(message)
        return await step_context.end_dialog()


    @staticmethod
    async def _show_warning_for_unsupported_cities(
        context: TurnContext, luis_result: BookingDetails
    ) -> None:
        """
        Shows a warning if the requested From or To cities are recognized as entities but they are not in the Airport entity list.
        In some cases LUIS will recognize the From and To composite entities as a valid cities but the From and To Airport values
        will be empty if those entity values can't be mapped to a canonical item in the Airport.
        """
        if luis_result.unsupported_airports:
            message_text = (
                f"Sorry but the following airports are not supported: "
                f"{', '.join(luis_result.unsupported_airports)}. "
                f"Please provide the name of a city."
            )
            message = MessageFactory.text(
                message_text, message_text, InputHints.ignoring_input
            )
            await context.send_activity(message)


    def create_confirm_card(self, title) -> Attachment:
        card = HeroCard(
            title=title,
            #images=[
            #    CardImage(
            #        url="https://findicons.com/files/icons/1014/ivista/128/good_or_tick.png"
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