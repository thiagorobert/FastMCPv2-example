import pytest
import time
import json
import base64
import hashlib
from unittest.mock import patch
from fastapi.testclient import TestClient
from authlib.jose import JsonWebToken
import urllib.parse

from oauth import (
    app, clients, authorization_codes, access_tokens, refresh_tokens,
    generate_client_credentials, generate_authorization_code,
    generate_access_token, generate_refresh_token,
    verify_code_challenge,
    ISSUER, private_key_pem, key_id
)


def create_code_challenge_verifier():
    """Create PKCE code verifier and challenge for testing."""
    import secrets
    code_verifier = (
        base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("utf-8").rstrip("=")
    )
    code_challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode("utf-8")).digest())
        .decode("utf-8")
        .rstrip("=")
    )
    return code_verifier, code_challenge


class TestOAuthServer:
    """Test class for OAuth server functionality."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def sample_client(self):
        """Create a sample client for testing."""
        # Clear storage first
        clients.clear()
        authorization_codes.clear()
        access_tokens.clear()
        refresh_tokens.clear()

        client_id, client_secret = generate_client_credentials()
        client_data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "client_name": "test_client",
            "redirect_uris": ["http://localhost:8082/callback"],
            "grant_types": ["authorization_code"],
            "response_types": ["code"],
            "scope": "read write",
            "token_endpoint_auth_method": "client_secret_basic",
            "client_id_issued_at": int(time.time()),
            "client_secret_expires_at": 0,
        }
        clients[client_id] = client_data
        return client_data



class TestUtilityFunctions(TestOAuthServer):
    """Test utility functions."""

    def test_generate_client_credentials(self):
        """Test client credentials generation."""
        client_id, client_secret = generate_client_credentials()

        assert client_id.startswith("mcp_client_")
        assert len(client_id) > len("mcp_client_")
        assert len(client_secret) > 0

        # Test uniqueness
        client_id2, client_secret2 = generate_client_credentials()
        assert client_id != client_id2
        assert client_secret != client_secret2

    def test_generate_authorization_code(self):
        """Test authorization code generation."""
        code = generate_authorization_code()
        assert isinstance(code, str)
        assert len(code) > 0

        # Test uniqueness
        code2 = generate_authorization_code()
        assert code != code2

    def test_generate_access_token(self):
        """Test JWT access token generation."""
        client_id = "test_client"
        scope = "read write"
        resource = "http://localhost:8080"

        token = generate_access_token(client_id, scope, resource)

        # Verify it's a JWT token
        parts = token.split(".")
        assert len(parts) == 3

        # Decode and verify header
        header_decoded = base64.urlsafe_b64decode(parts[0] + "=" * (4 - len(parts[0]) % 4))
        header = json.loads(header_decoded)
        assert header["alg"] == "RS256"
        assert header["typ"] == "JWT"
        assert header["kid"] == key_id

        # Decode and verify payload
        payload_decoded = base64.urlsafe_b64decode(parts[1] + "=" * (4 - len(parts[1]) % 4))
        payload = json.loads(payload_decoded)
        assert payload["iss"] == ISSUER
        assert payload["sub"] == client_id
        assert payload["client_id"] == client_id
        assert payload["aud"] == resource
        assert payload["scope"] == scope
        assert "iat" in payload
        assert "exp" in payload

    def test_generate_access_token_with_default_audience(self):
        """Test JWT access token generation with default audience."""
        client_id = "test_client"
        scope = "read write"

        token = generate_access_token(client_id, scope)

        parts = token.split(".")
        payload_decoded = base64.urlsafe_b64decode(parts[1] + "=" * (4 - len(parts[1]) % 4))
        payload = json.loads(payload_decoded)
        assert payload["aud"] == "http://localhost:8080"

    def test_generate_refresh_token(self):
        """Test refresh token generation."""
        token = generate_refresh_token()
        assert isinstance(token, str)
        assert len(token) > 0

        # Test uniqueness
        token2 = generate_refresh_token()
        assert token != token2

    def test_verify_code_challenge(self):
        """Test PKCE code challenge verification."""
        verifier, challenge = create_code_challenge_verifier()

        # Valid verification
        assert verify_code_challenge(verifier, challenge) is True

        # Invalid verification
        assert verify_code_challenge("wrong_verifier", challenge) is False
        assert verify_code_challenge(verifier, "wrong_challenge") is False


class TestAuthorizationServerMetadata(TestOAuthServer):
    """Test authorization server metadata endpoint."""

    def test_authorization_server_metadata(self, client):
        """Test OAuth 2.0 Authorization Server Metadata endpoint."""
        # Clear storage
        clients.clear()
        authorization_codes.clear()
        access_tokens.clear()
        refresh_tokens.clear()

        response = client.get("/.well-known/oauth-authorization-server")
        assert response.status_code == 200

        data = response.json()
        assert data["issuer"] == ISSUER
        assert "authorization_endpoint" in data
        assert "token_endpoint" in data
        assert "registration_endpoint" in data
        assert "jwks_uri" in data
        assert "code" in data["response_types_supported"]
        assert "authorization_code" in data["grant_types_supported"]
        assert "refresh_token" in data["grant_types_supported"]
        assert "S256" in data["code_challenge_methods_supported"]


class TestDynamicClientRegistration(TestOAuthServer):
    """Test dynamic client registration."""

    def test_client_registration_success(self, client):
        """Test successful client registration."""
        # Clear storage
        clients.clear()
        authorization_codes.clear()
        access_tokens.clear()
        refresh_tokens.clear()

        registration_data = {
            "client_name": "test_client",
            "redirect_uris": ["http://localhost:8082/callback"]
        }

        response = client.post("/oauth/register", json=registration_data)
        assert response.status_code == 200

        data = response.json()
        assert "client_id" in data
        assert "client_secret" in data
        assert data["client_name"] == "test_client"
        assert data["redirect_uris"] == ["http://localhost:8082/callback"]
        assert data["grant_types"] == ["authorization_code"]
        assert data["response_types"] == ["code"]
        assert data["token_endpoint_auth_method"] == "client_secret_basic"

        # Verify client is stored
        assert data["client_id"] in clients

    def test_client_registration_with_optional_params(self, client):
        """Test client registration with optional parameters."""
        # Clear storage
        clients.clear()
        authorization_codes.clear()
        access_tokens.clear()
        refresh_tokens.clear()

        registration_data = {
            "client_name": "advanced_client",
            "redirect_uris": ["http://localhost:8082/callback", "http://localhost:8083/callback"],
            "grant_types": ["authorization_code", "refresh_token"],
            "response_types": ["code"],
            "scope": "read write admin",
            "token_endpoint_auth_method": "client_secret_post"
        }

        response = client.post("/oauth/register", json=registration_data)
        assert response.status_code == 200

        data = response.json()
        assert data["grant_types"] == ["authorization_code", "refresh_token"]
        assert data["scope"] == "read write admin"
        assert data["token_endpoint_auth_method"] == "client_secret_post"


class TestAuthorizationEndpoint(TestOAuthServer):
    """Test authorization endpoint."""

    def test_authorization_success(self, client, sample_client):
        """Test successful authorization request."""
        params = {
            "response_type": "code",
            "client_id": sample_client["client_id"],
            "redirect_uri": sample_client["redirect_uris"][0],
            "scope": "read write",
            "state": "test_state"
        }

        response = client.get("/oauth/authorize", params=params, follow_redirects=False)
        assert response.status_code == 307  # Redirect

        location = response.headers["location"]
        parsed_url = urllib.parse.urlparse(location)
        query_params = urllib.parse.parse_qs(parsed_url.query)

        assert "code" in query_params
        assert query_params["state"][0] == "test_state"

        # Verify authorization code is stored
        code = query_params["code"][0]
        assert code in authorization_codes

    def test_authorization_with_pkce(self, client, sample_client):
        """Test authorization request with PKCE."""
        verifier, challenge = create_code_challenge_verifier()

        params = {
            "response_type": "code",
            "client_id": sample_client["client_id"],
            "redirect_uri": sample_client["redirect_uris"][0],
            "scope": "read write",
            "code_challenge": challenge,
            "code_challenge_method": "S256"
        }

        response = client.get("/oauth/authorize", params=params, follow_redirects=False)
        assert response.status_code == 307

        location = response.headers["location"]
        parsed_url = urllib.parse.urlparse(location)
        query_params = urllib.parse.parse_qs(parsed_url.query)

        code = query_params["code"][0]
        auth_data = authorization_codes[code]
        assert auth_data["code_challenge"] == challenge
        assert auth_data["code_challenge_method"] == "S256"

    def test_authorization_invalid_client(self, client):
        """Test authorization with invalid client."""
        params = {
            "response_type": "code",
            "client_id": "invalid_client",
            "redirect_uri": "http://localhost:8082/callback",
            "scope": "read write"
        }

        response = client.get("/oauth/authorize", params=params, follow_redirects=False)
        assert response.status_code == 400

    def test_authorization_invalid_redirect_uri(self, client, sample_client):
        """Test authorization with invalid redirect URI."""
        params = {
            "response_type": "code",
            "client_id": sample_client["client_id"],
            "redirect_uri": "http://malicious.com/callback",
            "scope": "read write"
        }

        response = client.get("/oauth/authorize", params=params, follow_redirects=False)
        assert response.status_code == 400

    def test_authorization_unsupported_response_type(self, client, sample_client):
        """Test authorization with unsupported response type."""
        params = {
            "response_type": "token",
            "client_id": sample_client["client_id"],
            "redirect_uri": sample_client["redirect_uris"][0],
            "scope": "read write",
            "state": "test_state"
        }

        response = client.get("/oauth/authorize", params=params, follow_redirects=False)
        assert response.status_code == 307

        location = response.headers["location"]
        parsed_url = urllib.parse.urlparse(location)
        query_params = urllib.parse.parse_qs(parsed_url.query)

        assert query_params["error"][0] == "unsupported_response_type"
        assert query_params["state"][0] == "test_state"


class TestTokenEndpoint(TestOAuthServer):
    """Test token endpoint."""

    @pytest.fixture
    def auth_code_data(self, sample_client):
        """Create authorization code data for testing."""
        code = generate_authorization_code()
        auth_data = {
            "client_id": sample_client["client_id"],
            "redirect_uri": sample_client["redirect_uris"][0],
            "scope": "read write",
            "code_challenge": None,
            "code_challenge_method": None,
            "resource": None,
            "expires_at": time.time() + 600,
            "used": False,
        }
        authorization_codes[code] = auth_data
        return code, auth_data

    def test_authorization_code_grant_success(self, client, sample_client, auth_code_data):
        """Test successful authorization code grant."""
        code, auth_data = auth_code_data

        form_data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": auth_data["redirect_uri"],
            "client_id": sample_client["client_id"],
            "client_secret": sample_client["client_secret"]
        }

        response = client.post("/oauth/token", data=form_data)
        assert response.status_code == 200

        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "Bearer"
        assert data["expires_in"] == 3600
        assert data["scope"] == "read write"

        # Verify JWT token
        access_token = data["access_token"]
        parts = access_token.split(".")
        assert len(parts) == 3

        # Verify code is marked as used
        assert authorization_codes[code]["used"] is True

    def test_authorization_code_grant_with_pkce(self, client, sample_client):
        """Test authorization code grant with PKCE."""
        verifier, challenge = create_code_challenge_verifier()
        code = generate_authorization_code()

        auth_data = {
            "client_id": sample_client["client_id"],
            "redirect_uri": sample_client["redirect_uris"][0],
            "scope": "read write",
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "resource": None,
            "expires_at": time.time() + 600,
            "used": False,
        }
        authorization_codes[code] = auth_data

        form_data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": auth_data["redirect_uri"],
            "client_id": sample_client["client_id"],
            "client_secret": sample_client["client_secret"],
            "code_verifier": verifier
        }

        response = client.post("/oauth/token", data=form_data)
        assert response.status_code == 200

    def test_authorization_code_grant_invalid_code(self, client, sample_client):
        """Test authorization code grant with invalid code."""
        form_data = {
            "grant_type": "authorization_code",
            "code": "invalid_code",
            "redirect_uri": "http://localhost:8082/callback",
            "client_id": sample_client["client_id"],
            "client_secret": sample_client["client_secret"]
        }

        response = client.post("/oauth/token", data=form_data)
        assert response.status_code == 400

    def test_authorization_code_grant_expired_code(self, client, sample_client):
        """Test authorization code grant with expired code."""
        code = generate_authorization_code()
        auth_data = {
            "client_id": sample_client["client_id"],
            "redirect_uri": sample_client["redirect_uris"][0],
            "scope": "read write",
            "code_challenge": None,
            "code_challenge_method": None,
            "resource": None,
            "expires_at": time.time() - 100,  # Expired
            "used": False,
        }
        authorization_codes[code] = auth_data

        form_data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": auth_data["redirect_uri"],
            "client_id": sample_client["client_id"],
            "client_secret": sample_client["client_secret"]
        }

        response = client.post("/oauth/token", data=form_data)
        assert response.status_code == 400

    def test_authorization_code_grant_used_code(self, client, sample_client, auth_code_data):
        """Test authorization code grant with already used code."""
        code, auth_data = auth_code_data
        auth_data["used"] = True

        form_data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": auth_data["redirect_uri"],
            "client_id": sample_client["client_id"],
            "client_secret": sample_client["client_secret"]
        }

        response = client.post("/oauth/token", data=form_data)
        assert response.status_code == 400

    def test_authorization_code_grant_client_mismatch(self, client, sample_client, auth_code_data):
        """Test authorization code grant with client mismatch."""
        code, auth_data = auth_code_data

        form_data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": auth_data["redirect_uri"],
            "client_id": "wrong_client_id",
            "client_secret": sample_client["client_secret"]
        }

        response = client.post("/oauth/token", data=form_data)
        assert response.status_code == 400

    def test_authorization_code_grant_invalid_client_secret(self, client, sample_client, auth_code_data):
        """Test authorization code grant with invalid client secret."""
        code, auth_data = auth_code_data

        form_data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": auth_data["redirect_uri"],
            "client_id": sample_client["client_id"],
            "client_secret": "wrong_secret"
        }

        response = client.post("/oauth/token", data=form_data)
        assert response.status_code == 401

    def test_authorization_code_grant_redirect_uri_mismatch(self, client, sample_client, auth_code_data):
        """Test authorization code grant with redirect URI mismatch."""
        code, auth_data = auth_code_data

        form_data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": "http://wrong-redirect.com/callback",
            "client_id": sample_client["client_id"],
            "client_secret": sample_client["client_secret"]
        }

        response = client.post("/oauth/token", data=form_data)
        assert response.status_code == 400

    def test_authorization_code_grant_missing_code_verifier(self, client, sample_client):
        """Test authorization code grant missing PKCE code verifier."""
        verifier, challenge = create_code_challenge_verifier()
        code = generate_authorization_code()

        auth_data = {
            "client_id": sample_client["client_id"],
            "redirect_uri": sample_client["redirect_uris"][0],
            "scope": "read write",
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "resource": None,
            "expires_at": time.time() + 600,
            "used": False,
        }
        authorization_codes[code] = auth_data

        form_data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": auth_data["redirect_uri"],
            "client_id": sample_client["client_id"],
            "client_secret": sample_client["client_secret"]
            # Missing code_verifier
        }

        response = client.post("/oauth/token", data=form_data)
        assert response.status_code == 400

    def test_authorization_code_grant_invalid_code_verifier(self, client, sample_client):
        """Test authorization code grant with invalid PKCE code verifier."""
        verifier, challenge = create_code_challenge_verifier()
        code = generate_authorization_code()

        auth_data = {
            "client_id": sample_client["client_id"],
            "redirect_uri": sample_client["redirect_uris"][0],
            "scope": "read write",
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "resource": None,
            "expires_at": time.time() + 600,
            "used": False,
        }
        authorization_codes[code] = auth_data

        form_data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": auth_data["redirect_uri"],
            "client_id": sample_client["client_id"],
            "client_secret": sample_client["client_secret"],
            "code_verifier": "wrong_verifier"
        }

        response = client.post("/oauth/token", data=form_data)
        assert response.status_code == 400

    def test_authorization_code_grant_client_not_found(self, client):
        """Test authorization code grant with client not found in clients dict."""
        code = generate_authorization_code()
        auth_data = {
            "client_id": "client_not_in_dict",
            "redirect_uri": "http://localhost:8082/callback",
            "scope": "read write",
            "code_challenge": None,
            "code_challenge_method": None,
            "resource": None,
            "expires_at": time.time() + 600,
            "used": False,
        }
        authorization_codes[code] = auth_data

        form_data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": auth_data["redirect_uri"],
            "client_id": "client_not_in_dict",
            "client_secret": "some_secret"
        }

        response = client.post("/oauth/token", data=form_data)
        assert response.status_code == 400

    def test_refresh_token_grant_success(self, client, sample_client):
        """Test successful refresh token grant."""
        # First create a refresh token
        refresh_token_val = generate_refresh_token()
        refresh_data = {
            "client_id": sample_client["client_id"],
            "scope": "read write",
            "resource": None,
            "expires_at": time.time() + 86400,
        }
        refresh_tokens[refresh_token_val] = refresh_data

        form_data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token_val,
            "client_id": sample_client["client_id"],
            "client_secret": sample_client["client_secret"]
        }

        response = client.post("/oauth/token", data=form_data)
        assert response.status_code == 200

        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "Bearer"
        assert data["expires_in"] == 3600
        assert data["scope"] == "read write"

    def test_refresh_token_grant_invalid_token(self, client, sample_client):
        """Test refresh token grant with invalid token."""
        form_data = {
            "grant_type": "refresh_token",
            "refresh_token": "invalid_refresh_token",
            "client_id": sample_client["client_id"],
            "client_secret": sample_client["client_secret"]
        }

        response = client.post("/oauth/token", data=form_data)
        assert response.status_code == 400

    def test_refresh_token_grant_expired_token(self, client, sample_client):
        """Test refresh token grant with expired token."""
        refresh_token_val = generate_refresh_token()
        refresh_data = {
            "client_id": sample_client["client_id"],
            "scope": "read write",
            "resource": None,
            "expires_at": time.time() - 100,  # Expired
        }
        refresh_tokens[refresh_token_val] = refresh_data

        form_data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token_val,
            "client_id": sample_client["client_id"],
            "client_secret": sample_client["client_secret"]
        }

        response = client.post("/oauth/token", data=form_data)
        assert response.status_code == 400

    def test_refresh_token_grant_client_mismatch(self, client, sample_client):
        """Test refresh token grant with client ID mismatch."""
        refresh_token_val = generate_refresh_token()
        refresh_data = {
            "client_id": "different_client_id",
            "scope": "read write",
            "resource": None,
            "expires_at": time.time() + 86400,
        }
        refresh_tokens[refresh_token_val] = refresh_data

        form_data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token_val,
            "client_id": sample_client["client_id"],
            "client_secret": sample_client["client_secret"]
        }

        response = client.post("/oauth/token", data=form_data)
        assert response.status_code == 400

    def test_refresh_token_grant_invalid_client(self, client):
        """Test refresh token grant with non-existent client."""
        refresh_token_val = generate_refresh_token()
        refresh_data = {
            "client_id": "nonexistent_client",
            "scope": "read write",
            "resource": None,
            "expires_at": time.time() + 86400,
        }
        refresh_tokens[refresh_token_val] = refresh_data

        form_data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token_val,
            "client_id": "nonexistent_client",
            "client_secret": "some_secret"
        }

        response = client.post("/oauth/token", data=form_data)
        assert response.status_code == 400

    def test_refresh_token_grant_invalid_client_secret_in_refresh(self, client, sample_client):
        """Test refresh token grant with invalid client secret."""
        refresh_token_val = generate_refresh_token()
        refresh_data = {
            "client_id": sample_client["client_id"],
            "scope": "read write",
            "resource": None,
            "expires_at": time.time() + 86400,
        }
        refresh_tokens[refresh_token_val] = refresh_data

        form_data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token_val,
            "client_id": sample_client["client_id"],
            "client_secret": "wrong_secret"
        }

        response = client.post("/oauth/token", data=form_data)
        assert response.status_code == 401

    def test_unsupported_grant_type(self, client, sample_client):
        """Test token endpoint with unsupported grant type."""
        form_data = {
            "grant_type": "client_credentials",
            "client_id": sample_client["client_id"],
            "client_secret": sample_client["client_secret"]
        }

        response = client.post("/oauth/token", data=form_data)
        assert response.status_code == 400


class TestTokenValidation(TestOAuthServer):
    """Test token validation endpoint."""

    @pytest.fixture
    def valid_access_token(self, sample_client):
        """Create a valid access token for testing."""
        token = generate_access_token(sample_client["client_id"], "read write")
        token_data = {
            "client_id": sample_client["client_id"],
            "scope": "read write",
            "resource": None,
            "expires_at": time.time() + 3600,
            "token_type": "Bearer",
        }
        access_tokens[token] = token_data
        return token, token_data

    def test_validate_token_success(self, client, valid_access_token):
        """Test successful token validation."""
        token, token_data = valid_access_token

        response = client.get("/oauth/validate", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200

        data = response.json()
        assert data["active"] is True
        assert data["client_id"] == token_data["client_id"]
        assert data["scope"] == token_data["scope"]

    def test_validate_token_invalid(self, client):
        """Test token validation with invalid token."""
        response = client.get("/oauth/validate", headers={"Authorization": "Bearer invalid_token"})
        assert response.status_code == 401

    def test_validate_token_expired(self, client, sample_client):
        """Test token validation with expired token."""
        token = generate_access_token(sample_client["client_id"], "read write")
        token_data = {
            "client_id": sample_client["client_id"],
            "scope": "read write",
            "resource": None,
            "expires_at": time.time() - 100,  # Expired
            "token_type": "Bearer",
        }
        access_tokens[token] = token_data

        response = client.get("/oauth/validate", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 401

    def test_validate_token_missing_header(self, client):
        """Test token validation without authorization header."""
        response = client.get("/oauth/validate")
        assert response.status_code == 403


class TestJWKSEndpoint(TestOAuthServer):
    """Test JWKS endpoint."""

    def test_jwks_endpoint(self, client):
        """Test JWKS endpoint returns proper key information."""
        response = client.get("/.well-known/jwks.json")
        assert response.status_code == 200

        data = response.json()
        assert "keys" in data
        assert len(data["keys"]) == 1

        key = data["keys"][0]
        assert key["kty"] == "RSA"
        assert key["kid"] == key_id
        assert key["use"] == "sig"
        assert key["alg"] == "RS256"
        assert "n" in key  # RSA modulus
        assert "e" in key  # RSA exponent

    def test_public_key_endpoint(self, client):
        """Test public key endpoint returns PEM format."""
        response = client.get("/debug/publickey")
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; charset=utf-8"

        pem_content = response.text
        assert pem_content.startswith("-----BEGIN PUBLIC KEY-----")
        assert pem_content.endswith("-----END PUBLIC KEY-----\n")
        assert "MII" in pem_content  # Base64 content indicator

    def test_single_jwk_endpoint(self, client):
        """Test single JWK endpoint for jwt.io compatibility."""
        response = client.get("/debug/jwk")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

        jwk = response.json()
        assert jwk["kty"] == "RSA"
        assert jwk["kid"] == key_id
        assert jwk["use"] == "sig"
        assert jwk["alg"] == "RS256"
        assert "n" in jwk  # RSA modulus
        assert "e" in jwk  # RSA exponent

        # Verify it's a single JWK object, not wrapped in "keys" array
        assert "keys" not in jwk

    def test_debug_clients_endpoint_empty(self, client):
        """Test debug clients endpoint when no clients are registered."""
        clients.clear()
        response = client.get("/debug/clients")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

        data = response.json()
        assert data["total_clients"] == 0
        assert data["clients"] == []

    def test_debug_clients_endpoint_with_clients(self, client):
        """Test debug clients endpoint with registered clients."""
        clients.clear()
        # Register a client first
        client_data = {
            "client_name": "Test Client",
            "redirect_uris": ["http://localhost:8082/callback"],
            "grant_types": ["authorization_code"],
            "scope": "read write"
        }

        reg_response = client.post("/oauth/register", json=client_data)
        assert reg_response.status_code == 200
        registered_client = reg_response.json()

        # Now test the debug endpoint
        response = client.get("/debug/clients")
        assert response.status_code == 200

        data = response.json()
        assert data["total_clients"] == 1
        assert len(data["clients"]) == 1

        client_info = data["clients"][0]
        assert client_info["client_id"] == registered_client["client_id"]
        assert client_info["client_name"] == "Test Client"
        assert client_info["redirect_uris"] == ["http://localhost:8082/callback"]
        assert client_info["grant_types"] == ["authorization_code"]
        assert client_info["scope"] == "read write"
        assert "client_id_issued_at" in client_info


class TestRootEndpoint(TestOAuthServer):
    """Test root endpoint."""

    def test_root_endpoint(self, client):
        """Test root endpoint returns HTML information."""
        response = client.get("/")
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/html; charset=utf-8"
        assert "MCP OAuth 2.1 Authorization Server" in response.text


class TestJWTTokenValidation:
    """Test JWT token validation using authlib directly."""

    def test_jwt_token_signature_validation(self):
        """Test that generated JWT tokens have valid signatures."""
        client_id = "test_client"
        scope = "read write"
        token = generate_access_token(client_id, scope)

        # Verify token signature using the same JWT library
        jwt_verifier = JsonWebToken(["RS256"])

        try:
            claims = jwt_verifier.decode(token, private_key_pem)
            assert claims["sub"] == client_id
            assert claims["scope"] == scope
            assert claims["iss"] == ISSUER
        except Exception as e:
            pytest.fail(f"JWT token validation failed: {e}")

    def test_jwt_token_expiration(self):
        """Test JWT token expiration claim."""
        client_id = "test_client"
        scope = "read write"

        # Mock time to control token generation
        with patch('oauth.time.time', return_value=1000000):
            token = generate_access_token(client_id, scope)

        jwt_verifier = JsonWebToken(["RS256"])
        claims = jwt_verifier.decode(token, private_key_pem)

        assert claims["iat"] == 1000000
        assert claims["exp"] == 1000000 + 3600  # 1 hour later


if __name__ == "__main__":
    pytest.main([__file__])