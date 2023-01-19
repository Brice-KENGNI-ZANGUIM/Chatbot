# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
from enum import Enum
from typing import Dict
from botbuilder.ai.luis import LuisRecognizer
from botbuilder.core import IntentScore, TopIntent, TurnContext

from booking_details import BookingDetails


class Intent(Enum):
    BOOK_FLIGHT = "BookFlight"
    CANCEL = "Utilities_Cancel"
    STOP = "Utilities_Stop"
    NONE_INTENT = "None"


def top_intent(intents: Dict[Intent, dict]) -> TopIntent:
    max_intent = Intent.NONE_INTENT
    max_value = 0.0

    for intent, value in intents:
        intent_score = IntentScore(value)
        if intent_score.score > max_value:
            max_intent, max_value = intent, intent_score.score

    return TopIntent(max_intent, max_value)


class LuisHelper:
    @staticmethod
    async def execute_luis_query(
        luis_recognizer: LuisRecognizer, turn_context: TurnContext
    ) -> (Intent, object):
        """
        Returns an object with preformatted LUIS results for the bot's dialogs to consume.
        """
        result = None
        intent = None

        try:
            recognizer_result = await luis_recognizer.recognize(turn_context)

            intent = (
                sorted(
                    recognizer_result.intents,
                    key=recognizer_result.intents.get,
                    reverse=True,
                )[:1][0]
                if recognizer_result.intents
                else None
            )

            result = BookingDetails()

            if (intent == Intent.CANCEL.value) | (intent == Intent.STOP.value):
                result.text = recognizer_result.text
                

            if intent == Intent.BOOK_FLIGHT.value:

                result.text = recognizer_result.text

                # Données géographiques
                geo_entities = recognizer_result.entities.get("geographyV2_city", [])
                to_entities = recognizer_result.entities.get("$instance", {}).get("dst_city", [])
                from_entities = recognizer_result.entities.get("$instance", {}).get("or_city", [])
                # Les entitées nommées doivent se trouver dans les données géographiques de VILLES
                # Toute autre donnée géographique trouvée est labellisée "Unsupported airport"
                if to_entities and not geo_entities:
                    result.unsupported_airports.append(to_entities[0]["text"].capitalize())
                if from_entities and not geo_entities:
                    result.unsupported_airports.append(from_entities[0]["text"].capitalize())
                if geo_entities:
                    if len(to_entities) > 0:
                        if to_entities[0]["text"] in geo_entities:
                            result.destination = to_entities[0]["text"].capitalize()
                        else:
                            result.unsupported_airports.append(to_entities[0]["text"].capitalize())
                    if len(from_entities) > 0:
                        if from_entities[0]["text"] in geo_entities:
                            result.origin = from_entities[0]["text"].capitalize()
                        else:
                            result.unsupported_airports.append(from_entities[0]["text"].capitalize())

                # Données temporelles
                date_entities = recognizer_result.entities.get("datetime", [])
                if date_entities:
                    # Récupération des chaînes Timex (datetime)
                    timex = []
                    for dte in date_entities:
                        t = dte['timex'][0]
                        if len(t) > 0:
                            if t.find('T') != -1:
                                timex.append(t.split('T')[0])
                            else:
                                timex.append(t)
                    if len(timex) > 0:
                        # Tri des dates par ordre chronologique             
                        timex.sort()
                        start_entities = recognizer_result.entities.get("$instance", {}).get("str_date", [])
                        end_entities = recognizer_result.entities.get("$instance", {}).get("end_date", [])
                        # Les dates Timex sont affectées en fonction des entités nommées trouvées
                        if len(timex) == 2:
                            result.travel_date = timex[0]
                            result.return_date = timex[1]
                        elif (len(timex) == 1):
                            if (len(start_entities) > 0):
                                result.travel_date = timex[0]
                            elif (len(end_entities) > 0):
                                result.return_date = timex[0]
                            else:
                                result.travel_date = timex[0]
                
                # Budget
                budget_entities = recognizer_result.entities.get("$instance", {}).get("budget", [])
                money_entities = recognizer_result.entities.get("$instance", {}).get("money", [])
                if (len(budget_entities) > 0) and (len(money_entities) > 0):
                    for i, j in enumerate(budget_entities):
                        for x, y in enumerate(money_entities):
                            bud_idx = budget_entities[i]['startIndex']
                            num_idx = money_entities[x]['startIndex']
                            if abs(bud_idx - num_idx) <= 3:
                                result.budget = money_entities[x]["text"]
                                result.amount = recognizer_result.entities.get("money", {})[x].get("number", 0)

        except Exception as exception:
            pass
        finally:
            return intent, result
