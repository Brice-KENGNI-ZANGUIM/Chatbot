#!/usr/bin/env python
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""Configuration for the bot."""

import os


class DefaultConfig:
    """Configuration for the bot."""

    PORT = 8000  
    
    APP_ID = os.environ.get("MS_APP_ID", "2df90819-fae7-4672-b618-05312220c8fa")
    APP_PASSWORD = os.environ.get("MS_APP_PASSWORD", "Z54D20vzX3k.aoJcdSiZfvuohRCYfFq4KbQ71CM5dftPvfBgAC8n294")
    
    LUIS_APP_ID = os.environ.get("LUIS_APP_ID", "3df7a534-4312-4590-9775-347a2a13ba87")
    LUIS_API_KEY = os.environ.get("LUIS_API_KEY", "9fefab7ed17d498280849ddfb3b76fa0")
    LUIS_API_HOST_NAME = os.environ.get("LUIS_API_HOSTNAME", "westeurope.api.cognitive.microsoft.com")
    
    APPINSIGHTS_INSTRUMENTATION_KEY = os.environ.get("APP_INSIGHT_INSTRUMENTATION_KEY", "dfd0528d-bc19-41d9-acf8-7a0f5e5b482d")
    TEQUILA_KIWI_API_KEY = os.environ.get("TEQUILA_KIWI_API_KEY", "fuwgIOd_zIUDReKpxyeB0QX6AJA2lDF1")
