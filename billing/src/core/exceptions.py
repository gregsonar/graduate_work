from typing import Any
from http import HTTPStatus


class BaseError(Exception):
    ...


class BaseErrorWithContent(BaseError):
    status_code: int
    content: dict[str, Any]


class AlreadySubscribedError(BaseErrorWithContent):
    status_code = HTTPStatus.CONFLICT
    content = {'message': 'User is already subscribed'}


class TariffNotFoundError(BaseErrorWithContent):
    status_code = HTTPStatus.NOT_FOUND
    content = {'message': 'Tariff is not found'}


class UserUnauthorizedError(BaseErrorWithContent):
    status_code = HTTPStatus.UNAUTHORIZED
    content = {'message': 'User is unauthorized'}


class RefundError(BaseErrorWithContent):
    status_code = HTTPStatus.BAD_REQUEST
    content = {'message': 'Refund was not created'}


class SubscriptionNotFoundError(BaseErrorWithContent):
    status_code = HTTPStatus.NOT_FOUND
    content = {'message': "User doesn't have subscription"}


class UserDoesntHaveRightsError(BaseErrorWithContent):
    status_code = HTTPStatus.CONFLICT
    content = {'message': "User doesn't have rights"}


class AuthServiceNoResponse(BaseErrorWithContent):
    status_code = HTTPStatus.BAD_GATEWAY
    content = {'message': 'Auth service doesn\'t reply'}


class AuthServiceBadResponse(BaseErrorWithContent):
    status_code = HTTPStatus.BAD_REQUEST
    content = {'message': 'Subscription wasn\'t be created in auth service'}