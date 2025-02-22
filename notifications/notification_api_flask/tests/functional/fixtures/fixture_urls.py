from pytest import fixture


@fixture
def rule_url(config):
    return f"{config.api_url}/rule"


@fixture
def message_url(config):
    return f"{config.api_url}/instant_message"
