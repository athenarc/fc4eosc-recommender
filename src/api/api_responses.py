
RECOMMENDATION_RESPONSES = {
        200: {
            "description": "Successful Response",
            "content": {
                "application/json": {
                    "examples": {
                        "zbmath": {
                            "summary": "zbMATH",
                            "value": {
                                "recommendations": [1269879,6108362,3676599,4175761,3388013,6012134,4036505,1915628,4050295,6958725]
                            }
                        },
                        "transport-research": {
                            "summary": "Transport Research",
                            "value": {
                                "recommendations": ["50|doi_dedup___::55b821fac5c8c7c6dd34efae11caa9e4","50|doi_dedup___::23eb8dfaa9dae5ab08ded5f1feb52bc2","50|doi_dedup___::c816292a4c3167fd696e26fe6d46d8fa","50|doi_________::9bb5d19c2e007a3d1270471a972ef5fa","50|doi_dedup___::284dc7963c5fe3c7a4a4eb30f318314e","50|doi_dedup___::7c3ea5d1742b8bdbf7948ea2c1f8e089","50|doi_________::e3ffc9022c2c4f8f77c572fe9eb6b38b","50|doi_dedup___::f3170e91ad9b8ce8845d417d5d0db035","50|doi_dedup___::1f12c9a7672c59e94785631a23833586","50|doi_dedup___::45c1eed69d106bc8a66429e4846227dc"]
                            }
                        },
                        "digital-humanities-and-cultural-heritage": {
                            "summary": "Digital Humanities and Cultural Heritage",
                            "value": {
                                "recommendations": ["50|doi_dedup___::9c6eec14384dfd9c17d1356e5d403c5d","50|doi_________::0530c3367c2dd6010752c43bae62acbc","50|doi_________::69bfcfa032b25ffde4e01dba2c8561f5","50|doi_dedup___::400493e0c6450c10cbef44b8a88ec475","50|doi_dedup___::ce5751978707a57655c539cdd875af2b","50|doi_________::c5c5fc9ce242b54a2a29e0b9b38cf7e7","50|doi_________::5f914b3b6febb7a36467bd7e659132dc","50|doi_dedup___::6c2cdc0fa3c305f9142731ae62830d28","50|doi_________::03a7e2a4cd5b7e3b3f2c71eb08725163","50|doi_________::ab4830c487240009f386771746086866"]
                            }
                        },
                        "energy-research": {
                            "summary": "Energy Research",
                            "value": {
                                "recommendations": ["50|doi_________::6c57664aaf34c203adb3ff824464d9e6","50|doi_________::1dd14736fa70b8a2f5c93819040f9b18","50|doi_________::afebf9c507f29ed0aad11803d86bd89d","50|doi_________::70808f99a0fdc8dc6c820b0c0dafe8b1","50|doi_dedup___::3a55a3a6792f4dd105158e41ca823f68","50|doi_dedup___::324eec922f26a096a8388a6ae8c26bbb","50|doi_dedup___::1f907ea00c6d1ab97ff15cc83f99ea0c","50|doi_dedup___::89b8270397346320485d7213b8b4c4eb","50|doi_________::14e29a67ed7d3000a73205030947f7b5","50|doi_dedup___::5d9e98cf3580f5c098739e42b7aad57a"]
                            }
                        }
                    }
                }
            }
        },
        422: {
            "description": "Validation Error",
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_community": {
                            "summary": "Invalid Community",
                            "value": {
                                "detail": [
                                    {
                                    "loc": ["path", "community"],
                                    "msg": "Input should be 'zbMATH', 'Transport Research', 'Digital Humanities and Cultural Heritage' or 'Energy Research'",
                                    "type": "enum",
                                    "input": "unknown community",
                                    "ctx": {
                                        "expected": "'zbMATH', 'Transport Research', 'Digital Humanities and Cultural Heritage' or 'Energy Research'"
                                        }
                                    }
                                ]
                            }
                        }
                    }
                }
            }
        }
    }

NEIGHBOR_RESPONSES = {
        200: {
            "description": "Successful Response",
            "content": {
                "application/json": {
                    "examples": {
                        "zbmath": {
                            "summary": "zbMATH",
                            "value": {
                                "neighbors": [6788699,6816280,6697481,6420664,6932290,5900670,5641602,6873073,6003009,5070761]
                            }
                        },
                        "transport-research": {
                            "summary": "Transport Research",
                            "value": {
                                "neighbors": ["50|doi_________::25af2a4c484d8baca732001f4e8620bf","50|doi_dedup___::dc9200fba1263539d0b55251678930df","50|doi_dedup___::6412d86e70837afdd7d4be6bdc07b16e","50|doi_dedup___::d721073ce7b23e71b81866f640b97121","50|doi_dedup___::2be56591182c8dad836ba90fb4ac1edc","50|doi_________::128815fea594bbeb78ba0ef0280d4b81","50|doi_dedup___::de4d0299b98af155725bd2a8fdcd4780","50|dedup_wf_001::ff191ec228712da51d1d77c17f2c09ad","50|doi_dedup___::6dee159a5e53e500acbb41d4a9067d13","50|doi_dedup___::3bd08c4dfff6a5523b27bcb9962e48fc"]
                            }
                        },
                        "digital-humanities-and-cultural-heritage": {
                            "summary": "Digital Humanities and Cultural Heritage",
                            "value": {
                                "recommendations": ["50|doi_dedup___::b04aa0c981a841e94aa84dfc6f37b022","50|doi_dedup___::c969801766f4a70611487b58e9402b61","50|doi_________::e6ef51c0ea8342c938a4cdea80c0e00e","50|doi_________::a8f791c2e20d8fc06565aa06be3a255d","50|doi_dedup___::06a50cb3832e0e1db468abd7e4323cea","50|doi_________::66ffbeef89b3a1d0b10b4660f990f9fb","50|doi_________::14e779ec74992cef3debf8d393914c25","50|doi_________::f23d7d7bba63ecaf91e19df74fc1ed76","50|doi_dedup___::55c312cabdf37068a803c0b4f84c0694","50|doi_dedup___::fb54086c3fb98dc1b20566b0e4abd143"]
                            }
                        },
                        "energy-research": {
                            "summary": "Energy Research",
                            "value": {
                                "recommendations": ["50|doi_dedup___::ad80322dc54a8ff093564e5b012c8b16","50|doi_dedup___::31e4aa310a44d5f7c2cde747e8fcb1da","50|doi_________::2ac0605475ee71919aa1c343bdc3c5f4","50|doi_dedup___::6e3dc48f793eeb23a89fc274143eb4f9","50|doi_________::10e42fda6d55b6295794cc1a2bf13e3d","50|doi_________::7d679b4c9358d56311831e43c9a7efec","50|doi_________::40a4cffb33ba43eb6beca1101e031601","50|doi_dedup___::031534148fb4a744a14da7bf7b3e515b","50|doi_________::1a287589f534f0f5984682142123adc1","50|doi_________::d3eb69536c691d9e7a55cb69f1b7d825"]
                            }
                        }
                    }
                }
            }
        },
        422: {
            "description": "Validation Error",
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_community": {
                            "summary": "Invalid Community",
                            "value": {
                                "detail": [
                                    {
                                    "loc": ["path", "community"],
                                    "msg": "Input should be 'zbMATH', 'Transport Research', 'Digital Humanities and Cultural Heritage' or 'Energy Research'",
                                    "type": "enum",
                                    "input": "unknown community",
                                    "ctx": {
                                        "expected": "'zbMATH', 'Transport Research', 'Digital Humanities and Cultural Heritage' or 'Energy Research'"
                                        }
                                    }
                                ]
                            }
                        }
                    }
                }
            }
        }
    }