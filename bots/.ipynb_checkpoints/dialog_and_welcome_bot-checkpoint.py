# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""Main dialog to welcome users."""
import json
import os.path

from typing import List
from botbuilder.dialogs import Dialog
from botbuilder.core import (
    TurnContext,
    ### Added
    MessageFactory,
    ConversationState,
    UserState,
    BotTelemetryClient,
)
from botbuilder.schema import Activity, Attachment, ChannelAccount
### Added
from botbuilder.schema import InputHints
### Added
from flight_booking_recognizer import FlightBookingRecognizer
from helpers.activity_helper import create_activity_reply
from .dialog_bot import DialogBot


class DialogAndWelcomeBot(DialogBot):
    """Main dialog to welcome users."""

    def __init__(
        self,
        conversation_state: ConversationState,
        user_state: UserState,
        dialog: Dialog,
        telemetry_client: BotTelemetryClient,
        ### Added
        luis_recognizer: FlightBookingRecognizer
    ):
        super(DialogAndWelcomeBot, self).__init__(
            conversation_state, user_state, dialog, telemetry_client
        )
        self.telemetry_client = telemetry_client

        ### Added
        self._luis_recognizer = luis_recognizer

    ### Commented out
    """
    async def on_members_added_activity(
        self, members_added: List[ChannelAccount], turn_context: TurnContext
    ):
        for member in members_added:
            # Greet anyone that was not the target (recipient) of this message.
            # To learn more about Adaptive Cards, see https://aka.ms/msbot-adaptivecards
            # for more details.
            if member.id != turn_context.activity.recipient.id:
                welcome_card = self.create_adaptive_card_attachment()
                response = self.create_response(turn_context.activity, welcome_card)
                await turn_context.send_activity(response)
    """
    ### Added instead
    async def on_members_added_activity(
        self, members_added: List[ChannelAccount], turn_context: TurnContext
    ):
        if not self._luis_recognizer.is_configured:
            return await turn_context.send_activity(
                MessageFactory.text(
                    "NOTE: LUIS is not configured. To enable all capabilities, add 'LuisAppId', 'LuisAPIKey' and "
                    "'LuisAPIHostName' to the appsettings.json file.",
                    input_hint=InputHints.ignoring_input,
                )
            )
            #return await step_context.next(None)
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                return await turn_context.send_activity(
                    MessageFactory.text(
                        "What can I help you with today?",
                        input_hint=InputHints.expecting_input
                    )
                )
    


    def create_response(self, activity: Activity, attachment: Attachment):
        """Create an attachment message response."""
        response = create_activity_reply(activity)
        response.attachments = [attachment]
        return response

    # Load attachment from file.
    def create_adaptive_card_attachment(self):
        """Create an adaptive card."""
        relative_path = os.path.abspath(os.path.dirname(__file__))
        path = os.path.join(relative_path, "resources/welcomeCard.json")
        with open(path) as card_file:
            card = json.load(card_file)

        return Attachment(
            content_type="application/vnd.microsoft.card.adaptive", content=card
        )
