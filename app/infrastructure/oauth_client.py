"""
Generic OAuth 1.0a HTTP client.

This module provides a reusable OAuth 1.0a authenticated HTTP client
that can be used with any OAuth 1.0a API (Bricklink, Twitter, etc.).

Not Bricklink-specific - just handles OAuth signing and requests.
"""

import asyncio
from typing import Dict, Any, Optional
from requests_oauthlib import OAuth1Session
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
import logging

logger = logging.getLogger(__name__)


class OAuthConfig:
    """Configuration for OAuth 1.0a authentication."""

    def __init__(
        self,
        consumer_key: str,
        consumer_secret: str,
        resource_owner_key: str,
        resource_owner_secret: str,
    ):
        """
        Initialize OAuth configuration.

        Args:
            consumer_key: OAuth consumer key (app identifier)
            consumer_secret: OAuth consumer secret (app password)
            resource_owner_key: OAuth access token
            resource_owner_secret: OAuth access token secret
        """
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.resource_owner_key = resource_owner_key
        self.resource_owner_secret = resource_owner_secret

    def validate(self) -> None:
        """
        Validate that all required credentials are present.

        Raises:
            ValueError: If any credential is missing
        """
        if not all([
            self.consumer_key,
            self.consumer_secret,
            self.resource_owner_key,
            self.resource_owner_secret,
        ]):
            raise ValueError("All OAuth credentials must be provided")


class OAuthHTTPClient:
    """
    Generic HTTP client with OAuth 1.0a authentication.

    Handles OAuth signing, retries, and error handling.
    Not tied to any specific API.
    """

    def __init__(
        self,
        config: OAuthConfig,
        timeout: int = 30,
        max_retries: int = 3,
    ):
        """
        Initialize OAuth HTTP client.

        Args:
            config: OAuth configuration with credentials
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        config.validate()
        self.config = config
        self.timeout = timeout
        self.max_retries = max_retries

        # Create OAuth session (handles all signing automatically)
        self.session = OAuth1Session(
            client_key=config.consumer_key,
            client_secret=config.consumer_secret,
            resource_owner_key=config.resource_owner_key,
            resource_owner_secret=config.resource_owner_secret,
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        reraise=True,
    )
    async def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Make an authenticated GET request.

        Args:
            url: Full URL to request
            params: Query parameters
            headers: Additional headers

        Returns:
            Parsed JSON response

        Raises:
            ConnectionError: If request fails after retries
            TimeoutError: If request times out
            ValueError: If response is not valid JSON
        """
        # Don't log params - they may contain sensitive data
        logger.debug(f"OAuth GET: {url}")

        # Run blocking request in thread pool to not block event loop
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self.session.get(
                url,
                params=params,
                headers=headers,
                timeout=self.timeout,
            ),
        )

        logger.debug(f"Response status: {response.status_code}")

        # Let caller handle status codes - don't raise here
        response.raise_for_status()

        return response.json()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        reraise=True,
    )
    async def post(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Make an authenticated POST request.

        Args:
            url: Full URL to request
            data: Form data
            json: JSON body
            headers: Additional headers

        Returns:
            Parsed JSON response

        Raises:
            ConnectionError: If request fails after retries
            TimeoutError: If request times out
            ValueError: If response is not valid JSON
        """
        logger.debug(f"OAuth POST: {url}")

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self.session.post(
                url,
                data=data,
                json=json,
                headers=headers,
                timeout=self.timeout,
            ),
        )

        logger.debug(f"Response status: {response.status_code}")
        response.raise_for_status()

        return response.json()

    async def health_check(self, url: str) -> bool:
        """
        Check if the OAuth-protected endpoint is accessible.

        Args:
            url: URL to check

        Returns:
            True if accessible, False otherwise
        """
        try:
            await self.get(url)
            return True
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            return False

    def close(self) -> None:
        """Close the underlying HTTP session."""
        self.session.close()
