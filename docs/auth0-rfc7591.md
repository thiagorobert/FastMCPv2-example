# Auth0 configuration for RFC 7591:


## Set up Auth0

1. Create a [Auth0](http://auth0.com) account (name suggestion:`rfc7591-test`)
   * using the free tier will work (but it expires in 21 days)

1. Enable `OIDC Dynamic Application Registration` in Auth0
   * Setting -> Advanced

1. Enable Management API
   * doc https://auth0.com/docs/api/management/v2
   * Applications -> APIs

1. Get a management API access token
   * Applications -> APIs > Auth0 Management API -> API Explorer

1. Promote Github social connection to domain-level
   * doc https://auth0.com/docs/authenticate/identity-providers/promote-connections-to-domain-level
    ```
    curl --request PATCH \
        --url 'https://rfc7591-test.us.auth0.com/api/v2/connections/${GITHUB_CONNECTION_ID}' \
        --header 'authorization: Bearer ${AUTH0_MGMT_API_ACCESS_TOKEN}' \
        --header 'cache-control: no-cache' \
        --header 'content-type: application/json' \
        --data '{ "is_domain_connection": true }'
    ```


## Create main app

1. doc: https://auth0.com/docs/quickstart/webapp/python/interactive

1. use Auth0's [example code](https://github.com/auth0-samples/auth0-python-web-app/tree/master/01-Login) or the version in `mainapp`

1. create a `.venv` and install requirements
   ```
   python -m venv .venv --prompt rfc7591-client
   source .venv/bin/activate
   pip install -r mainapp/requirements.txt
   ```

1. create a `.env` file or export the following environment variables:
   ```
   AUTH0_CLIENT_ID
   AUTH0_CLIENT_SECRET
   AUTH0_DOMAIN
   APP_SECRET_KEY
   ```

1. run the app locally and ensure you can login/logout successfully using Github
   ```
   python mainapp/server.py
   ```

1. Log in using Github


## Example Client Registration request:

Assuming a properly configured Auth0 named `rfc7591-test`.

The `registration_endpoint` is listed within the OpenID Connect discovery metadata: https://rfc7591-test.us.auth0.com/.well-known/openid-configuration

Example request:

```
curl --request POST \
  --url 'https://rfc7591-test.us.auth0.com/oidc/register' \
  --header 'content-type: application/json' \
  --data '{"client_name":"My Dynamic Application","redirect_uris": ["http://127.0.0.1:3000/callback"]}'
```

After the request, note down `client_id` and `client_secret` and verify the appliation in auth0 dashboard in 'Applications -> Applications'.


## Login using the dynamic application's credentials

1. Regular OAuth using the dynamic application's `client_id` and `client_secret`
1. The redirect URI provided will be used for the OAuth callback
   * you can configure other URIs via Auth0's UI
