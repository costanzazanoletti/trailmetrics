# Authentication Service

This service interacts with frontend to perform user authentication through Strava OAuth2 and JWT.
It interacts with other services with API Key authenticated requests

## Set up

The application can run in Intellij or in Docker.

### Intellij set up

SpringBoot uses standard /src/resources/application.yml from classpath and property values are
loaded from .env file.
To ensure SpringBoot loads the environment variables check in application.yml

```
spring:
  config:
    import: optional:file:.env[.properties]
```

## Test

Tests run with Profile=Test, src/test/resources/application-test.yml and can run from Intellij and
from Maven plugin inside Intellij.
Ensure that .env file is present and that environment variables are loaded from .env file

### Docker set up

Before starting the container in docker you must create the jar file using maven `clean package`.

## RSA Authentication

Inside /config/keys there must be the files

- private.pem
- public.pem
  They can be created using OpenSSL

1. Generate a private key

```
openssl genpkey -algorithm RSA -out private_key.pem -aes256
```

2. Extract the public key

```
openssl rsa -pubout -in private_key.pem -out public_key.pem
```
