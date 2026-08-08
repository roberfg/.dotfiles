---
name: generate-api-requests
description: Generate REST Client (.requests.http) and Bruno (opencollection.yml + .yml requests) files from project API routes
---

## What it does

- Scans the current project to auto-detect the backend framework (Express, FastAPI, ASP.NET Core, Gin, Django, Spring Boot, etc.)
- Parses all route definitions from controllers, routers, decorators, attributes, or annotations
- Generates a `.requests.http` file at the project root with all endpoints in REST Client format
- Generates a Bruno collection under `.docs/bruno/` with an `opencollection.yml` root and individual `.yml` request files

## How it works

1. **Detect project name and framework**: Parse build files (`pom.xml` → `artifactId`, `package.json` → `name`, `build.gradle` → project name, `Cargo.toml` → `name`, etc.) to get the project name, and identify the framework (Express, FastAPI, ASP.NET Core, Gin, Django, Spring Boot, etc.)
2. **Find routes**: Search the codebase for route/endpoint definitions (e.g. `@app.get()`, `app.Get()`, `[HttpGet]`, `router.get()`, `@GetMapping`)
3. **Extract details**: For each route, extract the HTTP method, path, path parameters, query parameters, request body shape, and auth requirements

### Endpoint name generation

Map HTTP method → verb and extract the meaningful noun from the path:

| Method | Verb   |
|--------|---------|
| GET    | Get     |
| POST   | Create  |
| PUT    | Update  |
| PATCH  | Update  |
| DELETE | Delete  |

Rules
- Take the last non-parameter path segment as the noun
- Remove path parameters (`:id`, `{id}`) and query params
- Replace special characters (`/`, `-`, `_`) with spaces

| Route                       | Generated name  |
|----------------------------|------------------|
| `GET /ping`                | Get ping           |
| `GET /users?name=`         | Get users by params |
| `POST /users`              | Create user        |
| `GET /users/:id`           | Get user by id     |
| `PUT /users/:id`           | Update user by id  |
| `DELETE /users/:userId`    | Delete user by id   |
| `GET /products/:id/reviews`| Get reviews by product id |
4. **Generate REST Client file**: Create `{project-name}.requests.http` at the project root with proper `###` separators
5. **Generate Bruno collection**: Create `.docs/bruno/{project-name}/` with:
   - `opencollection.yml` — collection root config
   - `{endpoint-name}.yml` — one file per endpoint with the request definition

### `opencollection.yml` format

```yaml
opencollection: 1.0.0

info:
  name: "{project-name}"

bundled: false

extensions: {}
```

### Request `.yml` format

```yaml
info:
  name: "{endpoint-name}"
  type: http
  seq: {seq}

http:
  method: {METHOD}
  url: "{base-url}{path}"

settings:
  encodeUrl: true
```

## Output structure

```
{project-root}/
├── {project-name}.requests.http     # REST Client format
└── .docs/
    └── bruno/
        └── {project-name}/
            ├── opencollection.yml    # Collection metadata
            ├── Get ping.yml          # One .yml per endpoint
            ├── Create user.yml
            └── Delete user.yml
```

## When to use

Use this when you need to quickly bootstrap or update HTTP request files from existing API route definitions in a project.
