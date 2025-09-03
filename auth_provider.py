from enum import Enum

from fastmcp.server.auth import RemoteAuthProvider
from fastmcp.server.auth.providers.jwt import JWTVerifier
from pydantic import AnyHttpUrl


class AuthProvider(Enum):
    AUTH0 = "auth0"
    KEYCLOAK = "keycloak"
    LOCAL = "local"


class AuthProviderFactory:
    """Factory class for creating authentication providers."""

    AUTH0_DOMAIN = "https://rfc7591-test.us.auth0.com"
    KEYCLOAK_DOMAIN = "http://localhost:8081"
    KEYCLOAK_REALM = "rfc7591-realm"
    LOCAL_DOMAIN = "http://localhost:8001"

    @classmethod
    def create_auth0_provider(cls) -> RemoteAuthProvider:
        """Create Auth0 authentication provider."""
        token_verifier = JWTVerifier(
            jwks_uri=f"{cls.AUTH0_DOMAIN}/.well-known/jwks.json",
            issuer=f"{cls.AUTH0_DOMAIN}/",
        )

        return RemoteAuthProvider(
            token_verifier=token_verifier,
            authorization_servers=[AnyHttpUrl(cls.AUTH0_DOMAIN)],
            resource_server_url="https://github.com"
        )

    @classmethod
    def create_keycloak_provider(cls) -> RemoteAuthProvider:
        """Create Keycloak authentication provider."""
        token_verifier = JWTVerifier(
            jwks_uri=f"{cls.KEYCLOAK_DOMAIN}/realms/{cls.KEYCLOAK_REALM}/protocol/openid-connect/certs",
            issuer=f"{cls.KEYCLOAK_DOMAIN}/realms/{cls.KEYCLOAK_REALM}",
        )

        return RemoteAuthProvider(
            token_verifier=token_verifier,
            authorization_servers=[AnyHttpUrl(cls.KEYCLOAK_DOMAIN)],
            resource_server_url="https://github.com"
        )

    @classmethod
    def create_local_provider(cls) -> RemoteAuthProvider:
        """Create Local authentication provider."""
        token_verifier = JWTVerifier(
            jwks_uri=f"{cls.LOCAL_DOMAIN}/.well-known/jwks.json",
            issuer=f"{cls.LOCAL_DOMAIN}/",
        )

        return RemoteAuthProvider(
            token_verifier=token_verifier,
            authorization_servers=[AnyHttpUrl(cls.LOCAL_DOMAIN)],
            resource_server_url="https://github.com"
        )
    @classmethod
    def create_provider(cls, provider_type: AuthProvider) -> RemoteAuthProvider:
        """Create authentication provider based on type."""
        if provider_type == AuthProvider.AUTH0:
            return cls.create_auth0_provider()
        elif provider_type == AuthProvider.KEYCLOAK:
            return cls.create_keycloak_provider()
        elif provider_type == AuthProvider.LOCAL:
            return cls.create_local_provider()
        else:
            raise ValueError(f"Unsupported auth provider: {provider_type}")

    @classmethod
    def get_oauth_metadata_url(cls, provider_type: AuthProvider) -> str:
        """Get OAuth metadata URL for the specified provider."""
        if provider_type == AuthProvider.AUTH0:
            return f"{cls.AUTH0_DOMAIN}/.well-known/openid-configuration"
        elif provider_type == AuthProvider.KEYCLOAK:
            return f"{cls.KEYCLOAK_DOMAIN}/realms/{cls.KEYCLOAK_REALM}/.well-known/openid-configuration"
        elif provider_type == AuthProvider.LOCAL:
            return f"{cls.LOCAL_DOMAIN}/.well-known/oauth-authorization-server"
        else:
            raise ValueError(f"Unsupported auth provider: {provider_type}")
