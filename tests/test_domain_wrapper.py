import pytest
from unittest.mock import MagicMock
from datetime import datetime

from domain import WeatherApi, WeatherRepository, WeatherState, ApiError, User
from domain_wrapper import WeatherApiWithRepository, CachedWeatherApi


@pytest.fixture
def mock_weather_api():
    mock = MagicMock(spec=WeatherApi)

    def mock_get_weather(city, user):
        return WeatherState(
            time=datetime.now(),
            city=city,
            temperature=20.5,
            feels_like=19.0,
            pressure=1015,
            humidity=65
        )

    mock.get_weather.side_effect = mock_get_weather
    return mock


@pytest.fixture
def mock_weather_api_error():
    mock = MagicMock(spec=WeatherApi)

    def mock_get_weather(city, user):
        return ApiError("Error")

    mock.get_weather.side_effect = mock_get_weather
    return mock


@pytest.fixture
def mock_weather_repository():
    mock = MagicMock(spec=WeatherRepository)
    return mock


def test_weather_api_with_repository(mock_weather_api,
                                     mock_weather_repository):
    wrapped = WeatherApiWithRepository(
        mock_weather_api,
        mock_weather_repository
    )

    user = User(1, "")
    weather = wrapped.get_weather("London", user)
    mock_weather_repository.save_weather.assert_called_once_with(weather, user)


def test_weather_api_with_repository_error(mock_weather_api_error,
                                           mock_weather_repository):
    wrapped = WeatherApiWithRepository(
        mock_weather_api_error,
        mock_weather_repository
    )

    weather = wrapped.get_weather("London", User(1, ""))
    assert isinstance(weather, ApiError)
    assert not mock_weather_repository.save_weather.called


def test_cached_weather_api(mock_weather_api):
    wrapped = CachedWeatherApi(mock_weather_api, 2)

    user = User(1, "")
    weather1 = wrapped.get_weather("London", user)
    weather2 = wrapped.get_weather("London", user)
    assert weather1 is weather2

    weather3 = wrapped.get_weather("Moscow", user)
    assert weather1.time != weather3.time

    wrapped.cache["London"]["expire_time"] = 0

    weather4 = wrapped.get_weather("London", user)
    assert weather1.time != weather4.time
