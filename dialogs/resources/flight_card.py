FLIGHT_CARD_CONTENT = {
    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
    "version": "1.0",
    "type": "AdaptiveCard",
    "speak": "Your flight details",
    "body": [
        {
            "type": "TextBlock",
            "text": "Passengers",
            "weight": "Bolder",
            "wrap": True
        },
        {
            "type": "TextBlock",
            "text": "User",
            "separator": True,
            "wrap": True,
            "size": "Large",
            "weight": "Default"
        },
        {
            "type": "TextBlock",
            "text": "21-d226",
            "wrap": True,
            "size": "Small",
            "spacing": "None"
        },
        {
            "type": "TextBlock",
            "text": "Wed 30 May 2017",
            "weight": "Bolder",
            "spacing": "Large",
            "wrap": True
        },
        {
            "type": "ColumnSet",
            "separator": True,
            "columns": [
                {
                    "type": "Column",
                    "width": 1,
                    "items": [
                        {
                            "type": "TextBlock",
                            "text": "San Francisco",
                            "isSubtle": True,
                            "wrap": True,
                            "size": "Medium"
                        },
                        {
                            "type": "TextBlock",
                            "text": "United Sates",
                            "wrap": True,
                            "spacing": "None",
                            "horizontalAlignment": "Left",
                            "size": "Small"
                        }
                    ],
                    "spacing": "None"
                },
                {
                    "type": "Column",
                    "width": 1,
                    "items": [
                        {
                            "type": "TextBlock",
                            "text": "Amsterdam",
                            "horizontalAlignment": "Right",
                            "isSubtle": True,
                            "wrap": True,
                            "size": "Medium"
                        },
                        {
                            "type": "TextBlock",
                            "text": "Netherlands",
                            "wrap": True,
                            "horizontalAlignment": "Right",
                            "size": "Small",
                            "spacing": "None"
                        }
                    ]
                }
            ]
        },
        {
            "type": "ColumnSet",
            "spacing": "None",
            "columns": [
                {
                    "type": "Column",
                    "width": 1,
                    "items": [
                        {
                            "type": "TextBlock",
                            "size": "ExtraLarge",
                            "color": "Accent",
                            "text": "SFO",
                            "spacing": "None",
                            "wrap": True
                        }
                    ]
                },
                {
                    "type": "Column",
                    "width": "auto",
                    "items": [
                        {
                            "type": "Image",
                            "url": "https://adaptivecards.io/content/airplane.png",
                            "altText": "Airplane",
                            "size": "Small",
                            "spacing": "None"
                        }
                    ]
                },
                {
                    "type": "Column",
                    "width": 1,
                    "items": [
                        {
                            "type": "TextBlock",
                            "size": "ExtraLarge",
                            "color": "Accent",
                            "text": "AMS",
                            "horizontalAlignment": "Right",
                            "spacing": "None",
                            "wrap": True
                        }
                    ]
                }
            ]
        },
        {
            "type": "TextBlock",
            "text": "Sat 2 June 2017",
            "weight": "Bolder",
            "spacing": "Medium",
            "wrap": True
        },
        {
            "type": "ColumnSet",
            "separator": True,
            "columns": [
                {
                    "type": "Column",
                    "width": 1,
                    "items": [
                        {
                            "type": "TextBlock",
                            "text": "Amsterdam",
                            "isSubtle": True,
                            "wrap": True,
                            "size": "Medium"
                        },
                        {
                            "type": "TextBlock",
                            "text": "Netherlands",
                            "wrap": True,
                            "spacing": "None",
                            "horizontalAlignment": "Left",
                            "size": "Small"
                        }
                    ]
                },
                {
                    "type": "Column",
                    "width": 1,
                    "items": [
                        {
                            "type": "TextBlock",
                            "text": "San Francisco",
                            "horizontalAlignment": "Right",
                            "isSubtle": True,
                            "wrap": True,
                            "size": "Medium"
                        },
                        {
                            "type": "TextBlock",
                            "text": "United Sates",
                            "wrap": True,
                            "spacing": "None",
                            "horizontalAlignment": "Right",
                            "size": "Small"
                        }
                    ]
                }
            ]
        },
        {
            "type": "ColumnSet",
            "spacing": "None",
            "columns": [
                {
                    "type": "Column",
                    "width": 1,
                    "items": [
                        {
                            "type": "TextBlock",
                            "size": "ExtraLarge",
                            "color": "Accent",
                            "text": "AMS",
                            "spacing": "None",
                            "wrap": True
                        }
                    ]
                },
                {
                    "type": "Column",
                    "width": "auto",
                    "items": [
                        {
                            "type": "Image",
                            "url": "https://adaptivecards.io/content/airplane.png",
                            "altText": "Airplane",
                            "size": "Small",
                            "spacing": "None"
                        }
                    ]
                },
                {
                    "type": "Column",
                    "width": 1,
                    "items": [
                        {
                            "type": "TextBlock",
                            "size": "ExtraLarge",
                            "color": "Accent",
                            "text": "SFO",
                            "horizontalAlignment": "Right",
                            "spacing": "None",
                            "wrap": True
                        }
                    ]
                }
            ]
        },
        {
            "type": "ColumnSet",
            "spacing": "Medium",
            "columns": [
                {
                    "type": "Column",
                    "width": 1,
                    "items": [
                        {
                            "type": "TextBlock",
                            "text": "Fees",
                            "wrap": True,
                            "weight": "Bolder"
                        }
                    ]
                }
            ]
        },
        {
            "type": "ColumnSet",
            "columns": [
                {
                    "type": "Column",
                    "width": "stretch",
                    "items": [
                        {
                            "type": "TextBlock",
                            "text": "Total",
                            "size": "Medium",
                            "isSubtle": True,
                            "wrap": True
                        }
                    ]
                },
                {
                    "type": "Column",
                    "width": "stretch",
                    "items": [
                        {
                            "type": "TextBlock",
                            "horizontalAlignment": "Right",
                            "text": "$4032.54",
                            "size": "Medium",
                            "weight": "Bolder",
                            "wrap": True
                        }
                    ]
                }
            ],
            "separator": True
        }
    ]
}