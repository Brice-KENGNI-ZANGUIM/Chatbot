# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""Handle origin resolution for booking dialog."""

from botbuilder.core import MessageFactory, BotTelemetryClient, NullTelemetryClient
from botbuilder.dialogs import WaterfallDialog, DialogTurnResult, WaterfallStepContext
from botbuilder.dialogs.prompts import (
    TextPrompt,
    PromptOptions
)
from botbuilder.schema import InputHints
from .cancel_and_help_dialog import CancelAndHelpDialog
from flight_booking_recognizer import FlightBookingRecognizer
from helpers.luis_helper import LuisHelper
from conversation_records import ConversationRecords


class OriginResolverDialog(CancelAndHelpDialog):
    """Resolve the destination"""

    def __init__(
        self,
        luis_recognizer: FlightBookingRecognizer,
        dialog_id: str = None,
        telemetry_client: BotTelemetryClient = NullTelemetryClient(),
        conversation_records: ConversationRecords = ConversationRecords()
    ):
        super(OriginResolverDialog, self).__init__(
            luis_recognizer=luis_recognizer,
            dialog_id=(dialog_id or OriginResolverDialog.__name__),
            telemetry_client=telemetry_client,
            conversation_records=conversation_records
        )
        self.telemetry_client = telemetry_client
        self._luis_recognizer = luis_recognizer
        self.origin = None
        self._context = None

        origin_prompt = TextPrompt(TextPrompt.__name__)
        origin_prompt.telemetry_client = telemetry_client

        waterfall_dialog = WaterfallDialog(
            WaterfallDialog.__name__ + "2", [self.initial_step, self.checking_step, self.final_step]
        )
        waterfall_dialog.telemetry_client = telemetry_client

        self.add_dialog(origin_prompt)
        self.add_dialog(waterfall_dialog)
        self.initial_dialog_id = WaterfallDialog.__name__ + "2"


    async def initial_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Prompt for the origin."""
        prompt_msg = "From what city would you like to travel?"
        if self.origin is None:
            self.conversation_records.add_turn(prompt_msg)
            return await step_context.prompt(
                TextPrompt.__name__,
                PromptOptions(
                    prompt=MessageFactory.text(prompt_msg)
                ),
            )
        return await step_context.next(self.origin)


    async def checking_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        self._context = step_context.context
        if not await self.origin_validator():
            self.origin = None
            reprompt_msg = ("I'm sorry, for best results, please input the name of a city.")
            self.conversation_records.add_turn(reprompt_msg)
            message = MessageFactory.text(
                reprompt_msg, reprompt_msg, InputHints.ignoring_input
            )
            await step_context.context.send_activity(message)
            return await step_context.replace_dialog(self.id)
        return await step_context.next(self.origin)


    async def final_step(self, step_context: WaterfallStepContext):
        origin = self.origin
        self.origin = None
        return await step_context.end_dialog(origin)


    async def origin_validator(self) -> bool:
        intent, luis_result = await LuisHelper.execute_luis_query(
            self._luis_recognizer, self._context
        )
        if luis_result:
            self.conversation_records.add_turn(luis_result.text, False)
            if luis_result.destination is not None:
                self.origin = luis_result.destination
                return True
            elif luis_result.origin is not None:
                self.origin = luis_result.origin
                return True
        return False
        