from io import BytesIO

import pytest

from aidp_orchestration.product_owner_http import ProductOwnerHTTPApplication


def bare_application() -> ProductOwnerHTTPApplication:
    application = object.__new__(ProductOwnerHTTPApplication)
    application.maximum_body_bytes = 128
    return application


def test_form_parser_accepts_only_exact_bounded_urlencoded_input() -> None:
    application = bare_application()
    body = b"csrf=token&operation=ACCEPT&reason="
    environ: dict[str, object] = {
        "CONTENT_TYPE": "application/x-www-form-urlencoded",
        "CONTENT_LENGTH": str(len(body)),
        "wsgi.input": BytesIO(body),
    }
    assert application._form(environ) == {
        "csrf": ["token"], "operation": ["ACCEPT"], "reason": [""]
    }


@pytest.mark.parametrize(
    "environ",
    [
        {"CONTENT_TYPE": "text/plain", "CONTENT_LENGTH": "0", "wsgi.input": BytesIO()},
        {"CONTENT_TYPE": "application/x-www-form-urlencoded", "CONTENT_LENGTH": "129", "wsgi.input": BytesIO()},
        {"CONTENT_TYPE": "application/x-www-form-urlencoded", "CONTENT_LENGTH": "3", "wsgi.input": BytesIO(b"x=1")},
    ],
)
def test_form_parser_fails_closed(environ: dict[str, object]) -> None:
    with pytest.raises(PermissionError):
        bare_application()._form(environ)


def test_parameter_parser_rejects_duplicates_and_unexpected_fields() -> None:
    with pytest.raises(PermissionError):
        ProductOwnerHTTPApplication._one({"csrf": ["a", "b"]}, "csrf", maximum=32)
    with pytest.raises(PermissionError):
        ProductOwnerHTTPApplication._parameters("context=ok&role=owner", {"context"})
