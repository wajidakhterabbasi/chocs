from copy import copy

import pytest
import re
from typing import Callable

from chocs import (
    Application,
    RequestHandlerMiddleware,
    HttpMethod,
    HttpRequest,
    HttpResponse,
    HttpStatus,
    NotFoundError,
    Route,
    Router,
)


def test_route_parsing() -> None:
    route = Route("/example/{pattern}")
    assert route.match("/example/test")


def test_route_parsing_with_wildcards() -> None:
    route = Route("/example/{a}*")
    assert route.pattern == re.compile(r"^/example/([^/]+).*?$", re.I | re.M)
    assert route.match("/example/test/1/2/3")
    assert route.match("/example/11")


def test_route_is_wildcard() -> None:
    route = Route("*")

    assert route.is_wildcard
    assert route.pattern == re.compile(r"^.*?$", re.I | re.M)


def test_route_match() -> None:
    route = Route("/pets/{pet_id}")
    route = route.match("/pets/11a22")
    assert route["pet_id"] == "11a22"

    route = Route("/pets/{pet_id}")
    route = route.match("/pets/22")
    assert route._parameters == {"pet_id": 22}


def test_router() -> None:
    def test_controller() -> None:
        pass

    router = Router()
    router.append(Route("/pets/{pet_id}"), test_controller)
    router.append(Route("/pets"), test_controller)
    match = router.match("/pets/12")

    assert match[0]["pet_id"] == 12
    assert router.match("/pets")


def test_router_fail_matching() -> None:
    def test_controller():
        pass

    router = Router()
    router.append(Route("/pets/{pet_id}"), test_controller)
    with pytest.raises(NotFoundError):
        router.match("/pet/12")


def test_route_match_multiple_parameters() -> None:
    route = Route("/pets/{pet_id}/{category}")
    route = route.match("/pets/11a22/test")
    assert route["pet_id"] == "11a22"
    assert route["category"] == "test"


def test_router_prioritise_routes_with_no_wildcards() -> None:
    def test_controller():
        pass

    router = Router()
    router.append(Route("/pets/*"), test_controller)
    router.append(Route("/pets/{pet_id}"), test_controller)
    router.append(Route("*"), test_controller)

    route, controller = router.match("/pets/11a22")

    assert route.route == "/pets/{pet_id}"


http = Application()


@pytest.mark.parametrize(
    "router_decorator, method",
    [
        (http.get, HttpMethod.GET),
        (http.post, HttpMethod.POST),
        (http.put, HttpMethod.PUT),
        (http.patch, HttpMethod.PATCH),
        (http.options, HttpMethod.OPTIONS),
        (http.delete, HttpMethod.DELETE),
        (http.head, HttpMethod.HEAD),
    ],
)
def test_router_method(router_decorator: Callable, method: HttpMethod) -> None:
    ok_response = HttpResponse("OK", HttpStatus.OK)
    request = HttpRequest(method, "/pet")

    def noop():
        pass

    @router_decorator("/pet")
    def get_pet(req: HttpRequest) -> HttpResponse:
        return ok_response

    assert get_pet(HttpRequest(HttpMethod.GET)) == ok_response
    assert http(request) == ok_response


def test_router_not_found() -> None:
    app = Application()

    request = HttpRequest(HttpMethod.GET, "/petxxx")
    response = app(request)

    assert response.status_code == HttpStatus.NOT_FOUND


def test_can_copy_route() -> None:
    # given
    base_route = Route("/test/{parameter}")

    # when
    match_route = base_route.match("/test/test-1")
    route_copy = copy(match_route)

    # then
    assert match_route
    assert route_copy.attributes == match_route.attributes
    assert route_copy.route == match_route.route
    assert route_copy.parameters == match_route.parameters
