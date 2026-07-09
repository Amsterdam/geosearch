def postprocessing_add_openapi_cors_header(result, generator, request, public):
    responses = (
        result.get("paths", {}).get("/openapi.json", {}).get("get", {}).get("responses", {})
    )
    openapi_json_response = responses.get("200")
    if openapi_json_response is None:
        return result

    headers = openapi_json_response.setdefault("headers", {})
    headers.setdefault(
        "access-control-allow-origin",
        {
            "description": "Allows the OpenAPI document to be fetched cross-origin.",
            "schema": {
                "type": "string",
                "enum": ["*"],
            },
        },
    )
    return result
