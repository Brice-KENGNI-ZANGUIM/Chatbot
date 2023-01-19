import aiounittest
from botbuilder.core import (
    TurnContext,
    ConversationState,
    MemoryStorage
)
from botbuilder.core.adapters import TestAdapter
from botbuilder.dialogs import DialogSet, DialogTurnStatus
from config import DefaultConfig
from dialogs.booking_dialog import BookingDialog
from flight_booking_recognizer import FlightBookingRecognizer
from booking_details import BookingDetails
from helpers.luis_helper import Intent
from azure.cognitiveservices.language.luis.runtime import LUISRuntimeClient
from msrest.authentication import CognitiveServicesCredentials


class DummyTest(aiounittest.AsyncTestCase):
	
    def setUp(self):
        self.conf = DefaultConfig()
        client = LUISRuntimeClient(
            'https://' + self.conf.LUIS_API_HOST_NAME,
            CognitiveServicesCredentials(self.conf.LUIS_API_KEY)
        )
        request_1 = "I will like to travel from Douala to Dakar"
        request_2 = "I want to travel from Accra to Lagos for less than $4500"
        request_3 = "I don't want to book anymore thanks"
        request_4 = "I stay in Abidjan and and for 1800$ i'm planning a fly to Strasourg"
        
        self.response_1 = client.prediction.resolve(self.conf.LUIS_APP_ID, query=request_1)
        self.response_2 = client.prediction.resolve(self.conf.LUIS_APP_ID, query=request_2)
        self.response_3 = client.prediction.resolve(self.conf.LUIS_APP_ID, query=request_3)
        self.response_4 = client.prediction.resolve(self.conf.LUIS_APP_ID, query=request_4)
	
    def book_intent(self):
    	""" Les intentions des requêtes 1 et 2 doivent être identiques à Intent.BOOK_FLIGHT """
        
        self.assertEqual(self.response_1.top_scoring_intent.intent, Intent.BOOK_FLIGHT.value)
        self.assertEqual(self.response_2.top_scoring_intent.intent, Intent.BOOK_FLIGHT.value)
        self.assertEqual(self.response_4.top_scoring_intent.intent, Intent.BOOK_FLIGHT.value)
        
    def stop_intent(self):
        """The intent to request 3 should be Intent.STOP"""
        self.assertEqual(self.response_3.top_scoring_intent.intent, Intent.STOP.value)


    def test_origin(self):
        """
            La ville d'origine des requêtes 1 et 2 devrait être 'Douala'
            L'entité "Douala" doit être de type "builtin.geographyV2.city"
        """
        for e in self.response_1.entities:
            if e.type == "or_city":
                self.assertEqual(e.entity, "douala")
                break
                
        for e in self.response_2.entities:
            if e.type == "or_city":
                self.assertEqual(e.entity, "accra")
            if e.type == "builtin.geographyV2.city":
                self.assertEqual(e.entity, "accra")
                
        for e in self.response_4.entities:
            if e.type == "or_city":
                self.assertEqual(e.entity, "abidjan")
            if e.type == "builtin.geographyV2.city":
                self.assertEqual(e.entity, "abidjan")

    def test_destination(self):
        """
            Destination of requests 1 should be Douala
            Destination of requests 2 should be Lagos
            The entity "Douala" should be of type "builtin.geographyV2.city"
            The entity "Lagos" should be of type "builtin.geographyV2.countryRegion"
        """
        for e in self.response_1.entities:
            if e.type == "dst_city":
                self.assertEqual(e.entity, "dakar")
                break
                
        for e in self.response_2.entities:
            if e.type == "dst_city":
                self.assertEqual(e.entity, "lagos")
            if e.type == "builtin.geographyV2.countryRegion":
                self.assertEqual(e.entity, "lagos")
                
        for e in self.response_4.entities:
            if e.type == "dst_city":
                self.assertEqual(e.entity, "strasourg")
            if e.type == "builtin.geographyV2.countryRegion":
                self.assertEqual(e.entity, "strasourg")
    
    def test_budget(self):
        """Budget of request 2 should be $4500"""
        for e in self.response_2.entities:
            if e.type == "budget":
                self.assertEqual(e.entity, "$4500")
                break
                
        for e in self.response_4.entities:
            if e.type == "budget":
                self.assertEqual(e.entity, "1800$")


    async def test_booking_process(self):
        """
            Here we intend to test the BookingDialog flow of qestions & answers,
            up to the point where the last piece of information is asked of the client,
            just before an actual flight research is performed
        """

        async def exec_test(turn_context:TurnContext):
            dialog_context = await dialogs.create_context(turn_context)
            results = await dialog_context.continue_dialog()
            if (results.status == DialogTurnStatus.Empty):
                dialog_context.options = booking_details
                await dialog_context.begin_dialog(dialog_id, booking_details)
            elif results.status == DialogTurnStatus.Complete:
                reply = results.result
                await turn_context.send_activity(reply)
            await conv_state.save_changes(turn_context)

        dialog_id = BookingDialog.__name__ + "2"
        recognizer = FlightBookingRecognizer(self.conf)
        booking_dialog = BookingDialog(recognizer, dialog_id)

        conv_state = ConversationState(MemoryStorage())
        dialogs_state = conv_state.create_property("dialog-state")
        dialogs = DialogSet(dialogs_state)
        dialogs.add(booking_dialog)
        adapter = TestAdapter(exec_test)
        booking_details = BookingDetails()

        step1 = await adapter.test("I want to book a flight", "To what city would you like to travel?")
        step2 = await step1.test("Lagos", "From what city would you like to travel?")
        step3 = await step2.test("Accra", "What your budget for the fly ?")
        step4 = await step3.test("$4500", "When would you like to travel?")
        step5 = await step4.test("Tomorrow", "What would be the return date?")
        await step5.test("15 days from now", "How big is your purse?")
        

