# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""Handle budget resolution for booking dialog."""

from botbuilder.core import MessageFactory, BotTelemetryClient, NullTelemetryClient
from botbuilder.dialogs import WaterfallDialog, DialogTurnResult, WaterfallStepContext
from botbuilder.dialogs.prompts import (
    NumberPrompt,
    PromptValidatorContext,
    PromptOptions
)
from .cancel_and_help_dialog import CancelAndHelpDialog
from conversation_records import ConversationRecords


class BudgetResolverDialog(CancelAndHelpDialog):
    """Resolve the budget"""

    def __init__(
        self,
        dialog_id: str = None,
        telemetry_client: BotTelemetryClient = NullTelemetryClient(),
        conversation_records: ConversationRecords = ConversationRecords()
    ):
        super(BudgetResolverDialog, self).__init__(
            dialog_id=(dialog_id or BudgetResolverDialog.__name__),
            telemetry_client=telemetry_client,
            conversation_records=conversation_records
        )
        self.telemetry_client = telemetry_client

        budget_prompt = NumberPrompt(
            NumberPrompt.__name__, BudgetResolverDialog.number_prompt_validator
        )
        budget_prompt.telemetry_client = telemetry_client

        waterfall_dialog = WaterfallDialog(
            WaterfallDialog.__name__ + "2", [self.initial_step, self.final_step]
        )
        waterfall_dialog.telemetry_client = telemetry_client

        self.add_dialog(budget_prompt)
        self.add_dialog(waterfall_dialog)

        self.initial_dialog_id = WaterfallDialog.__name__ + "2"

    async def initial_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        """Prompt for the budget."""
        amount = step_context.options

        prompt_msg = "How big is your purse?"
        reprompt_msg = (
            "I'm sorry, for best results, please input a number using cyphers without trailing decimals nor currency symbol."
        )

        if amount is None:
            # We were not given any number at all so prompt the user.
            self.conversation_records.add_turn(prompt_msg)
            return await step_context.prompt(
                NumberPrompt.__name__,
                PromptOptions(  # pylint: disable=bad-continuation
                    prompt=MessageFactory.text(prompt_msg),
                    retry_prompt=MessageFactory.text(reprompt_msg),
                ),
            )

        # We have a budget we just need to check it is unambiguous.
        if type(amount) is float:
            # This is essentially a "reprompt" of the data we were given up front.
            return await step_context.prompt(
                NumberPrompt.__name__, PromptOptions(prompt=reprompt_msg)
            )

        return await step_context.next(amount)


    async def final_step(self, step_context: WaterfallStepContext):
        """Cleanup - set final return value and end dialog."""
        amount = step_context.result
        self.conversation_records.add_turn(amount, False)
        return await step_context.end_dialog(amount)


    @staticmethod
    async def number_prompt_validator(prompt_context: PromptValidatorContext) -> bool:
        """ Validate the number provided is in proper form. """
        if prompt_context.recognized.succeeded:
            try:
                budget = float(prompt_context.recognized.value)
            except ValueError:
                budget = "error"
            return type(budget) is float

        return False
