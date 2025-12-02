"""
Unit tests for the OAuth 1.0a HTTP client.

Tests OAuth configuration, request signing, retries, and error handling.
"""

from unittest.mock import patch

import pytest
from requests_oauthlib import OAuth1Session

from app.infrastructure.oauth_client import OAuthConfig, OAuthHTTPClient


class TestOAuthConfig:
    """Test OAuth configuration validation."""

    def test_valid_config(self, oauth_config):
        """Test that valid config doesn't raise."""
        oauth_config.validate()  # Should not raise

    def test_missing_consumer_key(self):
        """Test that missing consumer key raises ValueError."""
        config = OAuthConfig(
            consumer_key="",
            consumer_secret="secret",
            resource_owner_key="token",
            resource_owner_secret="token_secret",
        )
        with pytest.raises(ValueError, match="All OAuth credentials"):
            config.validate()

    def test_missing_consumer_secret(self):
        """Test that missing consumer secret raises ValueError."""
        config = OAuthConfig(
            consumer_key="key",
            consumer_secret="",
            resource_owner_key="token",
            resource_owner_secret="token_secret",
        )
        with pytest.raises(ValueError):
            config.validate()

    def test_all_missing(self):
        """Test that all missing credentials raises ValueError."""
        config = OAuthConfig(
            consumer_key="",
            consumer_secret="",
            resource_owner_key="",
            resource_owner_secret="",
        )
        with pytest.raises(ValueError):
            config.validate()


class TestOAuthHTTPClient:
    """Test OAuth HTTP client functionality."""

    def test_client_initialization(self, oauth_config):
        """Test that client initializes with valid config."""
        client = OAuthHTTPClient(oauth_config)
        assert client.config == oauth_config
        assert client.timeout == 30
        assert client.max_retries == 3
        assert isinstance(client.session, OAuth1Session)

    def test_client_custom_timeout(self, oauth_config):
        """Test that custom timeout is set."""
        client = OAuthHTTPClient(oauth_config, timeout=60)
        assert client.timeout == 60

    def test_client_validates_config(self):
        """Test that client validates config on init."""
        invalid_config = OAuthConfig("", "", "", "")
        with pytest.raises(ValueError):
            OAuthHTTPClient(invalid_config)

    @pytest.mark.asyncio
    async def test_get_request_success(self, oauth_config, mock_oauth_response):
        """Test successful GET request."""
        client = OAuthHTTPClient(oauth_config)

        expected_data = {"data": {"key": "value"}}
        mock_response = mock_oauth_response(expected_data, 200)

        with patch.object(client.session, "get", return_value=mock_response):
            result = await client.get("https://api.example.com/test")

            assert result == expected_data
            client.session.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_request_with_params(self, oauth_config, mock_oauth_response):
        """Test GET request with query parameters."""
        client = OAuthHTTPClient(oauth_config)

        expected_data = {"data": []}
        mock_response = mock_oauth_response(expected_data, 200)

        params = {"type": "SET", "limit": 10}

        with patch.object(client.session, "get", return_value=mock_response):
            result = await client.get("https://api.example.com/items", params=params)

            assert result == expected_data
            call_args = client.session.get.call_args
            assert call_args[1]["params"] == params

    @pytest.mark.asyncio
    async def test_get_request_with_headers(self, oauth_config, mock_oauth_response):
        """Test GET request with custom headers."""
        client = OAuthHTTPClient(oauth_config)

        expected_data = {"data": []}
        mock_response = mock_oauth_response(expected_data, 200)

        headers = {"Accept": "application/json"}

        with patch.object(client.session, "get", return_value=mock_response):
            result = await client.get("https://api.example.com/test", headers=headers)

            assert result == expected_data
            call_args = client.session.get.call_args
            assert call_args[1]["headers"] == headers

    @pytest.mark.asyncio
    async def test_get_request_http_error(self, oauth_config, mock_oauth_response):
        """Test GET request that returns HTTP error."""
        import requests

        client = OAuthHTTPClient(oauth_config)

        mock_response = mock_oauth_response({"error": "Not found"}, 404)

        with patch.object(client.session, "get", return_value=mock_response):
            with pytest.raises(requests.exceptions.HTTPError):
                await client.get("https://api.example.com/notfound")

    @pytest.mark.asyncio
    async def test_post_request_success(self, oauth_config, mock_oauth_response):
        """Test successful POST request."""
        client = OAuthHTTPClient(oauth_config)

        expected_data = {"data": {"created": True}}
        mock_response = mock_oauth_response(expected_data, 201)

        with patch.object(client.session, "post", return_value=mock_response):
            result = await client.post("https://api.example.com/create")

            assert result == expected_data
            client.session.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_post_request_with_json(self, oauth_config, mock_oauth_response):
        """Test POST request with JSON body."""
        client = OAuthHTTPClient(oauth_config)

        expected_data = {"success": True}
        mock_response = mock_oauth_response(expected_data, 200)

        json_data = {"name": "Test Set", "number": "12345"}

        with patch.object(client.session, "post", return_value=mock_response):
            result = await client.post("https://api.example.com/create", json=json_data)

            assert result == expected_data
            call_args = client.session.post.call_args
            assert call_args[1]["json"] == json_data

    @pytest.mark.asyncio
    async def test_health_check_success(self, oauth_config, mock_oauth_response):
        """Test health check with accessible endpoint."""
        client = OAuthHTTPClient(oauth_config)

        mock_response = mock_oauth_response({"status": "ok"}, 200)

        with patch.object(client.session, "get", return_value=mock_response):
            result = await client.health_check("https://api.example.com/health")

            assert result is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self, oauth_config, mock_oauth_response):
        """Test health check with inaccessible endpoint."""

        client = OAuthHTTPClient(oauth_config)

        mock_response = mock_oauth_response({"error": "Service unavailable"}, 503)

        with patch.object(client.session, "get", return_value=mock_response):
            result = await client.health_check("https://api.example.com/health")

            assert result is False

    def test_close_session(self, oauth_config):
        """Test that close() closes the underlying session."""
        client = OAuthHTTPClient(oauth_config)

        with patch.object(client.session, "close") as mock_close:
            client.close()
            mock_close.assert_called_once()
