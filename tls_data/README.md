# TLS data

This directory contains self-signed TLS data to support secure connections.

Generate the required files with command below.

```
> openssl req \
    -newkey rsa:2048 \
    -addext "subjectAltName = DNS:localhost" \
    -nodes \
    -x509 \
    -days 365 \
    -keyout server.key \
    -out server.crt
```
