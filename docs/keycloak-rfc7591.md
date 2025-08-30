# Keycloak configuration for RFC 7591:

## Set up Keycloak

1. Run it locally:

```
podman run \
  -p 8081:8080 \
  -e KEYCLOAK_ADMIN=admin \
  -e KEYCLOAK_ADMIN_PASSWORD=admin \
  quay.io/keycloak/keycloak:24.0.4 start-dev
```

1. Point your browser to http://localhost:8081 and log in with user `admin`, password `admin`

1. Create a new realm (name suggestion:`rfc7591-realm`)


## Enable Client Registration:

1. Go to "Clients" -> "Initial Access Tokens".
1. Create a new initial access token.
   * This token is used to authenticate the client registration request.
   * Settings:
      * Expiration: how long is the initial access token be valid
      * Count: how many dynamic clients can be created
   * The token value is displayed only once upon creation, so it must be copied immediately.


## Example Client Registration request:

Assuming Keycloak running at `http://localhost:8081` and a properly configured realm named `rfc7591-realm`

The `registration_endpoint` is listed within the OpenID Connect discovery metadata: http://localhost:8081/realms/rfc7591-realm/.well-known/openid-configuration

Example request:

```
curl --request POST \
  --url "http://localhost:8081/realms/rfc7591-realm/clients-registrations/openid-connect" \
  --header "content-type: application/json" \
  --header "Authorization: Bearer ${KEYCLOAK_INITIAL_ACCESS_TOKEN}" \
  --data '{"client_name":"My Dynamic Application","redirect_uris": ["http://127.0.0.1:3000/callback"]}'
```

After the request, note down `client_id` and `client_secret` and verify the appliation in Keycloak dashboard for your realm in 'Clients'.


## Login using the dynamic application's credentials

1. Regular OAuth using the dynamic application's `client_id` and `client_secret`
1. The redirect URI provided will be used for the OAuth callback
   * you can configure other URIs via auth0's UI
