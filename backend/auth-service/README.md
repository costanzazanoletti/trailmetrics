# Authentication Service

This service interacts with frontend to perform user authentication through Strava OAuth2 and JWT.
It interacts with other services with API Key authenticated requests

## Set up

The application can run in Intellij or in Docker.

### Intellij set up

Create a SpringBoot Configuration and enable Environment variables. Copy and paste the content of .env file into the variables panel.
SpringBoot uses standard /src/resources/application.yml from classpath
Tests run with src/test/resources/application-test.yml and can run from Intellij and from Maven plugin inside Intellij

### Docker set up

Docker has no access to classpath, so it uses the /config/application.yml, so the two files must be consistent.
Before starting the container in docker the application must be build with maven `clean package`

## RSA Authentication

Inside /config/keys there must be the files

- private.pem
- public.pem
  They can be created using OpenSSL

1. Generate a private key

```sh
openssl genpkey -algorithm RSA -out private_key.pem -aes256
```

2. Extract the public key

```sh
openssl rsa -pubout -in private_key.pem -out public_key.pem
```
