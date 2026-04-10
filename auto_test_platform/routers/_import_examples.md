## Swagger/OpenAPI 最小 JSON 示例（可导入）

```json
{
  "swagger": "2.0",
  "basePath": "/api",
  "paths": {
    "/users/{id}": {
      "get": {
        "summary": "获取用户",
        "parameters": [
          { "name": "id", "in": "path", "required": true, "type": "string" },
          { "name": "verbose", "in": "query", "required": false, "type": "boolean" }
        ]
      }
    },
    "/login": {
      "post": {
        "summary": "登录",
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "properties": {
                "username": { "type": "string" },
                "password": { "type": "string" }
              }
            }
          }
        ]
      }
    }
  }
}
```

## Postman 最小 JSON 示例（可导入）

```json
{
  "info": { "name": "Demo", "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json" },
  "item": [
    {
      "name": "Get Users",
      "request": {
        "method": "GET",
        "header": [{ "key": "Authorization", "value": "Bearer {{token}}" }],
        "url": { "raw": "{{base_url}}/api/users" }
      }
    },
    {
      "name": "Login",
      "request": {
        "method": "POST",
        "header": [{ "key": "Content-Type", "value": "application/json" }],
        "body": { "mode": "raw", "raw": "{\"username\":\"demo\",\"password\":\"123\"}" },
        "url": { "raw": "{{base_url}}/api/login" }
      }
    }
  ]
}
```

