# Authentication Service

This service handles user authentication via Strava OAuth2 and issues JWT tokens used by the frontend. It also validates tokens and serves public keys to other backend services. Internal service-to-service communication is secured with API Key authentication.

## Responsibilities

- Redirects users to Strava for OAuth2 authentication
- Exchanges authorization code for Strava access token
- Issues signed JWT tokens for authenticated users
- Exposes public key for JWT verification
- Validates incoming JWTs and API keys

## Dependencies

- Strava API (OAuth2 flow)
- PostgreSQL (user persistence)
- Other services (consume JWT and validate API key)

## Configuration

Configuration variables must be defined in a `.env` file. An example file is available at `.env.example`.

This includes:

- Auth service port and public key exposure
- API key used for internal authentication
- JWT cookie configuration
- Database connection
- RSA key locations

Spring Boot automatically loads these if the following is included in `application.yml`:

```yaml
spring:
  config:
    import: optional:file:.env[.properties]
```

## Building and Running

### From IntelliJ

1. Ensure `.env` file is present with required config (see `.env.example`)
2. Build using Maven: `clean package`
3. Run `AuthenticationServiceApplication` class directly

### With Docker

1. Build the jar with Maven:

```bash
./mvnw clean package
```

2. Start via Docker Compose:

```bash
docker compose up auth-service
```

## RSA Key Pair for JWT

JWTs are signed with a private RSA key and verified using the public key. Keys must be placed in the `config/keys` folder:

- `private.pem`
- `public.pem`

You can generate them with OpenSSL:

```bash
openssl genpkey -algorithm RSA -out private_key.pem -aes256
openssl rsa -pubout -in private_key.pem -out public_key.pem
```

Then rename and move the files:

```bash
mv private_key.pem config/keys/private.pem
mv public_key.pem config/keys/public.pem
```

## Tests

Unit and integration tests are included under `src/test/`. Run them using:

```bash
./mvnw test
```
