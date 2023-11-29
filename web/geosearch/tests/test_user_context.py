import json

import pytest
from flask import current_app as app
from flask import g

from datapunt_geosearch import db
from datapunt_geosearch.base_config import CLOUD_ENV

only_run_on_azure = pytest.mark.skipif(
    CLOUD_ENV.lower() != "azure", reason="End user context is only applicable on Azure"
)


@only_run_on_azure
def test_user_not_set_by_default(test_client, dataservices_db, dataservices_fake_data):
    """Prove that usercontext not set when not configured"""
    with test_client() as client:
        client.get("/?datasets=fake/fake_public&x=0&y=0")
        assert (
            db.dbconnection(
                app.config["DSN_DATASERVICES_DATASETS"], set_user_role=True
            )._active_user
            is None
        )


@only_run_on_azure
def test_anonymous_when_no_jwt(
    active_user_context,
    test_client,
    dataservices_db,
    dataservices_fake_data,
    role_configuration,
):
    with test_client() as client:
        response = client.get("/?x=123282.6&y=487674.8&radius=1&datasets=fake")
        json_response = json.loads(response.data)
        assert len(json_response["features"]) == 1
        assert (
            db.dbconnection(
                app.config["DSN_DATASERVICES_DATASETS"], set_user_role=True
            )._active_user
            == db.ANONYMOUS_ROLE
        )

    # The user context must be cleaned up when the request context is popped
    assert (
        db.dbconnection(app.config["DSN_DATASERVICES_DATASETS"], set_user_role=True)._active_user
        is None
    )


@only_run_on_azure
def test_end_user_when_jwt(
    active_user_context,
    test_client,
    dataservices_db,
    dataservices_fake_data,
    role_configuration,
    create_authz_token,
):
    with test_client() as client:
        jwt = create_authz_token(None, "test@test.nl", [])
        response = client.get(
            "/?x=123282.6&y=487674.8&radius=1&datasets=fake",
            headers={"Authorization": f"Bearer {jwt}"},
        )
        json_response = json.loads(response.data)
        assert len(json_response["features"]) == 1
        assert g.token_subject == "test@test.nl"
        assert (
            db.dbconnection(
                app.config["DSN_DATASERVICES_DATASETS"], set_user_role=True
            )._active_user
            == "test@test.nl_role"
        )

    # The user context must be cleaned up when the request context is popped
    assert (
        db.dbconnection(app.config["DSN_DATASERVICES_DATASETS"], set_user_role=True)._active_user
        is None
    )


@only_run_on_azure
def test_employee_when_internal_jwt_but_role_does_not_exist(
    active_user_context,
    test_client,
    dataservices_db,
    dataservices_fake_data,
    role_configuration,
    create_authz_token,
):
    with test_client() as client:
        jwt = create_authz_token(None, "test@amsterdam.nl", [])
        response = client.get(
            "/?x=123282.6&y=487674.8&radius=1&datasets=fake",
            headers={"Authorization": f"Bearer {jwt}"},
        )
        json_response = json.loads(response.data)
        assert len(json_response["features"]) == 1
        assert g.token_subject == "test@amsterdam.nl"
        assert (
            db.dbconnection(
                app.config["DSN_DATASERVICES_DATASETS"], set_user_role=True
            )._active_user
            == "medewerker_role"
        )
