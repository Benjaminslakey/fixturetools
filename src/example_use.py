import os
import pytest

from src.consumption import create_function_double
from src.production import create_fixtures


def function_one(arg1, arg2, *args, **kwargs):
    return ""


def function_two(arg1, **kwargs):
    return ""


FIXTURE_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), "fixtures")


@pytest.fixture
def function_one_double():
    path = os.path.join(FIXTURE_PATH, "function_one.json")
    return create_function_double(function_one, path)


@pytest.fixture
def function_two_double():
    path = os.path.join(FIXTURE_PATH, "function_two.json")
    return create_function_double(function_two, path)


@pytest.mark.unittest
def test_stuff(function_one_double, function_two_double):
    # arrange

    # act
    produce_fixtures_test()

    # assert
    assert True


@create_fixtures(['function_one', 'function_two'], output_dir=FIXTURE_PATH)
def produce_fixtures_test(*args, **kwargs):
    function_one()
    function_two()
    return {}


if __name__ == '__main__':
    produce_fixtures_test("random_value1", 2, another="value")
