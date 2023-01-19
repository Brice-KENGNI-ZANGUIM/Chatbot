# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""Handle cancel and help intents."""

from botbuilder.core import BotTelemetryClient, NullTelemetryClient
from botbuilder.dialogs import (
    ComponentDialog,
    DialogContext,
    DialogTurnResult,
    DialogTurnStatus,
)
from botbuilder.schema import ActivityTypes
from flight_booking_recognizer import FlightBookingRecognizer
from helpers.luis_helper import LuisHelper, Intent
from conversation_records import ConversationRecords


class CancelAndHelpDialog(ComponentDialog):
    """Implementation of handling cancel and help."""

    def __init__(
        self,
        luis_recognizer: FlightBookingRecognizer = None,
        dialog_id: str = None,
        telemetry_client: BotTelemetryClient = NullTelemetryClient(),
        conversation_records: ConversationRecords = ConversationRecords()
    ):
        super(CancelAndHelpDialog, self).__init__(dialog_id)
        self.telemetry_client = telemetry_client
        self._luis_recognizer = luis_recognizer
        self.conversation_records = conversation_records
        

    async def on_begin_dialog(self, inner_dc: DialogContext, options: object) -> DialogTurnResult:
        result = await self.interrupt(inner_dc)
        if result is not None:
            return result
        return await super(CancelAndHelpDialog, self).on_begin_dialog(inner_dc, options)


    async def on_continue_dialog(self, inner_dc: DialogContext) -> DialogTurnResult:
        result = await self.interrupt(inner_dc)
        if result is not None:
            return result
        return await super(CancelAndHelpDialog, self).on_continue_dialog(inner_dc)


    async def interrupt(self, inner_dc: DialogContext) -> DialogTurnResult:
        """Detect interruptions."""
        if inner_dc.context.activity.type == ActivityTypes.message:
            intent, luis_result = await LuisHelper.execute_luis_query(
                self._luis_recognizer, inner_dc.context
            )
            if intent:
                if (intent == Intent.STOP.value) or (intent == Intent.CANCEL.value):
                    self.conversation_records.add_turn(luis_result.text, False)
                    self.conversation_records.add_turn("Cancelling")
                    await inner_dc.context.send_activity("Cancelling")
                    return await inner_dc.cancel_all_dialogs()
        return None
