"""Multi-language API client code generation from OpenAPI snapshots."""

from __future__ import annotations

import re
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.services.contract_testing_service import contract_testing_service


class CodegenService:
    SUPPORTED = (
        "python",
        "javascript",
        "typescript",
        "java",
        "go",
        "curl",
        "csharp",
        "php",
        "ruby",
        "kotlin",
        "swift",
        "rust",
    )

    async def generate_from_snapshot(
        self,
        db: AsyncSession,
        *,
        snapshot_id: int,
        language: str,
        base_url: str = "https://api.example.com",
        class_name: str = "ApiClient",
    ) -> dict[str, Any]:
        language = (language or "python").lower()
        if language not in self.SUPPORTED:
            raise ValueError(f"unsupported language: {language}; supported={','.join(self.SUPPORTED)}")
        snapshot = await contract_testing_service.get_snapshot(db, snapshot_id)
        endpoints = list(snapshot.parsed_endpoints or [])
        if not endpoints:
            parsed = contract_testing_service.parse_openapi(snapshot.spec_content)
            endpoints = parsed.get("endpoints") or []
        code = self.render(language, endpoints, base_url=base_url, class_name=class_name)
        return {
            "language": language,
            "filename": self._filename(language, class_name),
            "code": code,
            "endpoint_count": len(endpoints),
            "snapshot_id": snapshot_id,
            "supported_languages": list(self.SUPPORTED),
        }

    def render(
        self,
        language: str,
        endpoints: list[dict[str, Any]],
        *,
        base_url: str,
        class_name: str,
    ) -> str:
        if language == "python":
            return self._python(endpoints, base_url, class_name)
        if language == "javascript":
            return self._javascript(endpoints, base_url, class_name, typescript=False)
        if language == "typescript":
            return self._javascript(endpoints, base_url, class_name, typescript=True)
        if language == "java":
            return self._java(endpoints, base_url, class_name)
        if language == "go":
            return self._go(endpoints, base_url, class_name)
        if language == "csharp":
            return self._csharp(endpoints, base_url, class_name)
        if language == "php":
            return self._php(endpoints, base_url, class_name)
        if language == "ruby":
            return self._ruby(endpoints, base_url, class_name)
        if language == "kotlin":
            return self._kotlin(endpoints, base_url, class_name)
        if language == "swift":
            return self._swift(endpoints, base_url, class_name)
        if language == "rust":
            return self._rust(endpoints, base_url, class_name)
        return self._curl(endpoints, base_url)

    def _safe_name(self, method: str, path: str, operation_id: str | None = None) -> str:
        if operation_id:
            name = re.sub(r"[^0-9a-zA-Z_]+", "_", operation_id)
            if name and name[0].isdigit():
                name = f"op_{name}"
            return name or "operation"
        parts = [p for p in re.split(r"[^0-9a-zA-Z]+", path) if p and not p.startswith("{")]
        return f"{method.lower()}_{'_'.join(parts) or 'root'}"

    def _python(self, endpoints: list[dict[str, Any]], base_url: str, class_name: str) -> str:
        lines = [
            "from __future__ import annotations",
            "",
            "from typing import Any",
            "",
            "import httpx",
            "",
            "",
            f"class {class_name}:",
            f'    def __init__(self, base_url: str = "{base_url}", token: str | None = None):',
            "        self.base_url = base_url.rstrip('/')",
            "        self.token = token",
            "",
            "    def _headers(self) -> dict[str, str]:",
            "        headers = {'Accept': 'application/json'}",
            "        if self.token:",
            "            headers['Authorization'] = f'Bearer {self.token}'",
            "        return headers",
            "",
        ]
        for ep in endpoints:
            method = str(ep.get("method") or "GET").upper()
            path = str(ep.get("path") or "/")
            name = self._safe_name(method, path, ep.get("operation_id"))
            path_params = re.findall(r"\{([^}/]+)\}", path)
            args = ["self"] + [f"{p}: str" for p in path_params]
            if method in {"POST", "PUT", "PATCH"}:
                args.append("body: dict[str, Any] | None = None")
            args.append("**params: Any")
            lines.append(f"    async def {name}({', '.join(args)}) -> Any:")
            lines.append(f'        """{ep.get("summary") or method + " " + path}"""')
            fmt_path = path
            for p in path_params:
                fmt_path = fmt_path.replace("{" + p + "}", "{" + p + "}")
            lines.append(f'        path = f"{fmt_path}"')
            if method in {"POST", "PUT", "PATCH"}:
                lines.append(
                    "        async with httpx.AsyncClient() as client:\n"
                    "            resp = await client.request(\n"
                    f'                "{method}", f"{{self.base_url}}{{path}}", headers=self._headers(), json=body, params=params or None\n'
                    "            )\n"
                    "            resp.raise_for_status()\n"
                    "            return resp.json() if resp.content else None"
                )
            else:
                lines.append(
                    "        async with httpx.AsyncClient() as client:\n"
                    "            resp = await client.request(\n"
                    f'                "{method}", f"{{self.base_url}}{{path}}", headers=self._headers(), params=params or None\n'
                    "            )\n"
                    "            resp.raise_for_status()\n"
                    "            return resp.json() if resp.content else None"
                )
            lines.append("")
        return "\n".join(lines)

    def _javascript(self, endpoints: list[dict[str, Any]], base_url: str, class_name: str, *, typescript: bool) -> str:
        t_any = ": any" if typescript else ""
        t_str = ": string" if typescript else ""
        t_ret = ": Promise<any>" if typescript else ""
        lines = [
            f"export class {class_name} {{",
            f"  constructor(baseUrl{t_str} = '{base_url}', token{t_str} | null = null) {{",
            "    this.baseUrl = baseUrl.replace(/\\/$/, '');",
            "    this.token = token;",
            "  }",
            "",
            f"  headers(){t_ret if False else ''} {{",
            "    const h = { Accept: 'application/json' };",
            "    if (this.token) h.Authorization = `Bearer ${this.token}`;",
            "    return h;",
            "  }",
            "",
        ]
        for ep in endpoints:
            method = str(ep.get("method") or "GET").upper()
            path = str(ep.get("path") or "/")
            name = self._safe_name(method, path, ep.get("operation_id"))
            path_params = re.findall(r"\{([^}/]+)\}", path)
            args = [f"{p}{t_str}" for p in path_params]
            if method in {"POST", "PUT", "PATCH"}:
                args.append(f"body{t_any} = null")
            args.append(f"params{t_any} = {{}}")
            lines.append(f"  async {name}({', '.join(args)}){t_ret} {{")
            js_path = path
            for p in path_params:
                js_path = js_path.replace("{" + p + "}", "${" + p + "}")
            lines.append(f"    const path = `{js_path}`;")
            lines.append("    const qs = new URLSearchParams(params || {}).toString();")
            lines.append("    const url = `${this.baseUrl}${path}${qs ? `?${qs}` : ''}`;")
            if method in {"POST", "PUT", "PATCH"}:
                lines.append(
                    f"    const res = await fetch(url, {{ method: '{method}', headers: {{ ...this.headers(), 'Content-Type': 'application/json' }}, body: body ? JSON.stringify(body) : undefined }});"
                )
            else:
                lines.append(f"    const res = await fetch(url, {{ method: '{method}', headers: this.headers() }});")
            lines.append("    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);")
            lines.append("    const text = await res.text();")
            lines.append("    return text ? JSON.parse(text) : null;")
            lines.append("  }")
            lines.append("")
        lines.append("}")
        lines.append("")
        return "\n".join(lines)

    def _java(self, endpoints: list[dict[str, Any]], base_url: str, class_name: str) -> str:
        lines = [
            "import java.net.URI;",
            "import java.net.http.HttpClient;",
            "import java.net.http.HttpRequest;",
            "import java.net.http.HttpResponse;",
            "",
            f"public class {class_name} {{",
            "  private final String baseUrl;",
            "  private final String token;",
            "  private final HttpClient client = HttpClient.newHttpClient();",
            "",
            f'  public {class_name}() {{ this("{base_url}", null); }}',
            f"  public {class_name}(String baseUrl, String token) {{",
            '    this.baseUrl = baseUrl.replaceAll("/+$", "");',
            "    this.token = token;",
            "  }",
            "",
        ]
        for ep in endpoints:
            method = str(ep.get("method") or "GET").upper()
            path = str(ep.get("path") or "/")
            name = self._safe_name(method, path, ep.get("operation_id"))
            lines.append(f"  public String {name}() throws Exception {{")
            lines.append(f'    HttpRequest.Builder b = HttpRequest.newBuilder(URI.create(baseUrl + "{path}"))')
            lines.append(f'        .method("{method}", HttpRequest.BodyPublishers.noBody())')
            lines.append('        .header("Accept", "application/json");')
            lines.append('    if (token != null) b.header("Authorization", "Bearer " + token);')
            lines.append(
                "    HttpResponse<String> resp = client.send(b.build(), HttpResponse.BodyHandlers.ofString());"
            )
            lines.append('    if (resp.statusCode() >= 400) throw new RuntimeException("HTTP " + resp.statusCode());')
            lines.append("    return resp.body();")
            lines.append("  }")
            lines.append("")
        lines.append("}")
        return "\n".join(lines)

    def _go(self, endpoints: list[dict[str, Any]], base_url: str, class_name: str) -> str:
        lines = [
            "package client",
            "",
            "import (",
            '  "fmt"',
            '  "io"',
            '  "net/http"',
            '  "strings"',
            ")",
            "",
            f"type {class_name} struct {{",
            "  BaseURL string",
            "  Token   string",
            "  Client  *http.Client",
            "}",
            "",
            f"func New{class_name}(baseURL, token string) *{class_name} {{",
            f'  if baseURL == "" {{ baseURL = "{base_url}" }}',
            f'  return &{class_name}{{BaseURL: strings.TrimRight(baseURL, "/"), Token: token, Client: http.DefaultClient}}',
            "}",
            "",
        ]
        for ep in endpoints:
            method = str(ep.get("method") or "GET").upper()
            path = str(ep.get("path") or "/")
            name = self._safe_name(method, path, ep.get("operation_id"))
            export = "".join(part[:1].upper() + part[1:] for part in name.split("_") if part)
            lines.append(f"func (c *{class_name}) {export}() ([]byte, error) {{")
            lines.append(f'  req, err := http.NewRequest("{method}", c.BaseURL+"{path}", nil)')
            lines.append("  if err != nil { return nil, err }")
            lines.append('  req.Header.Set("Accept", "application/json")')
            lines.append('  if c.Token != "" { req.Header.Set("Authorization", "Bearer "+c.Token) }')
            lines.append("  resp, err := c.Client.Do(req)")
            lines.append("  if err != nil { return nil, err }")
            lines.append("  defer resp.Body.Close()")
            lines.append("  body, err := io.ReadAll(resp.Body)")
            lines.append("  if err != nil { return nil, err }")
            lines.append(
                '  if resp.StatusCode >= 400 { return nil, fmt.Errorf("HTTP %d: %s", resp.StatusCode, string(body)) }'
            )
            lines.append("  return body, nil")
            lines.append("}")
            lines.append("")
        return "\n".join(lines)

    def _curl(self, endpoints: list[dict[str, Any]], base_url: str) -> str:
        lines = ["#!/usr/bin/env bash", f'BASE_URL="{base_url.rstrip("/")}"', "TOKEN=${TOKEN:-}", ""]
        for ep in endpoints:
            method = str(ep.get("method") or "GET").upper()
            path = str(ep.get("path") or "/")
            name = self._safe_name(method, path, ep.get("operation_id"))
            lines.append(f"# {name}: {method} {path}")
            lines.append(
                f'curl -sS -X {method} "$BASE_URL{path}" -H "Accept: application/json" ${{TOKEN:+-H "Authorization: Bearer $TOKEN"}}'
            )
            lines.append("")
        return "\n".join(lines)

    def _csharp(self, endpoints: list[dict[str, Any]], base_url: str, class_name: str) -> str:
        lines = [
            "using System.Net.Http.Headers;",
            "using System.Text;",
            "using System.Text.Json;",
            "",
            f"public class {class_name}",
            "{",
            "    private readonly HttpClient _client;",
            "    private readonly string _baseUrl;",
            "    private readonly string? _token;",
            "",
            f'    public {class_name}(string baseUrl = "{base_url}", string? token = null)',
            "    {",
            "        _baseUrl = baseUrl.TrimEnd('/');",
            "        _token = token;",
            "        _client = new HttpClient();",
            "    }",
            "",
        ]
        for ep in endpoints:
            method = str(ep.get("method") or "GET").upper()
            path = str(ep.get("path") or "/")
            name = self._safe_name(method, path, ep.get("operation_id"))
            lines.append(f"    public async Task<string> {name}()")
            lines.append("    {")
            lines.append(
                f'        using var req = new HttpRequestMessage(HttpMethod.{method.title() if method in {"GET", "POST", "PUT", "DELETE", "PATCH"} else "Get"}, _baseUrl + "{path}");'
            )
            lines.append('        req.Headers.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));')
            lines.append(
                '        if (!string.IsNullOrEmpty(_token)) req.Headers.Authorization = new AuthenticationHeaderValue("Bearer", _token);'
            )
            lines.append("        var resp = await _client.SendAsync(req);")
            lines.append("        resp.EnsureSuccessStatusCode();")
            lines.append("        return await resp.Content.ReadAsStringAsync();")
            lines.append("    }")
            lines.append("")
        lines.append("}")
        return "\n".join(lines)

    def _php(self, endpoints: list[dict[str, Any]], base_url: str, class_name: str) -> str:
        lines = [
            "<?php",
            f"class {class_name} {{",
            "    private string $baseUrl;",
            "    private ?string $token;",
            f'    public function __construct(string $baseUrl = "{base_url}", ?string $token = null) {{',
            "        $this->baseUrl = rtrim($baseUrl, '/');",
            "        $this->token = $token;",
            "    }",
            "    private function request(string $method, string $path): string {",
            "        $ch = curl_init($this->baseUrl . $path);",
            "        $headers = ['Accept: application/json'];",
            "        if ($this->token) $headers[] = 'Authorization: Bearer ' . $this->token;",
            "        curl_setopt_array($ch, [CURLOPT_CUSTOMREQUEST => $method, CURLOPT_RETURNTRANSFER => true, CURLOPT_HTTPHEADER => $headers]);",
            "        $body = curl_exec($ch);",
            "        if ($body === false) throw new RuntimeException(curl_error($ch));",
            "        curl_close($ch);",
            "        return $body;",
            "    }",
            "",
        ]
        for ep in endpoints:
            method = str(ep.get("method") or "GET").upper()
            path = str(ep.get("path") or "/")
            name = self._safe_name(method, path, ep.get("operation_id"))
            lines.append(f"    public function {name}(): string {{ return $this->request('{method}', '{path}'); }}")
        lines.append("}")
        return "\n".join(lines)

    def _ruby(self, endpoints: list[dict[str, Any]], base_url: str, class_name: str) -> str:
        lines = [
            "require 'net/http'",
            "require 'uri'",
            "require 'json'",
            "",
            f"class {class_name}",
            f"  def initialize(base_url = '{base_url}', token = nil)",
            "    @base_url = base_url.sub(/\\/+$/, '')",
            "    @token = token",
            "  end",
            "",
        ]
        for ep in endpoints:
            method = str(ep.get("method") or "GET").upper()
            path = str(ep.get("path") or "/")
            name = self._safe_name(method, path, ep.get("operation_id"))
            lines.append(f"  def {name}")
            lines.append(f"    uri = URI(@base_url + '{path}')")
            lines.append(f"    req = Net::HTTP::{method.capitalize()}.new(uri)")
            lines.append("    req['Accept'] = 'application/json'")
            lines.append("    req['Authorization'] = \"Bearer #{@token}\" if @token")
            lines.append(
                "    res = Net::HTTP.start(uri.hostname, uri.port, use_ssl: uri.scheme == 'https') { |http| http.request(req) }"
            )
            lines.append('    raise "HTTP #{res.code}" unless res.is_a?(Net::HTTPSuccess)')
            lines.append("    res.body")
            lines.append("  end")
            lines.append("")
        lines.append("end")
        return "\n".join(lines)

    def _kotlin(self, endpoints: list[dict[str, Any]], base_url: str, class_name: str) -> str:
        lines = [
            "import okhttp3.OkHttpClient",
            "import okhttp3.Request",
            "",
            f"class {class_name}(",
            f'    private val baseUrl: String = "{base_url}",',
            "    private val token: String? = null,",
            "    private val client: OkHttpClient = OkHttpClient()",
            ") {",
        ]
        for ep in endpoints:
            method = str(ep.get("method") or "GET").upper()
            path = str(ep.get("path") or "/")
            name = self._safe_name(method, path, ep.get("operation_id"))
            lines.append(f"    fun {name}(): String {{")
            lines.append(
                '        val builder = Request.Builder().url(baseUrl.trimEnd(\'/\') + "$path").method("$method", null)'
            )
            lines.append('        builder.header("Accept", "application/json")')
            lines.append('        if (token != null) builder.header("Authorization", "Bearer $token")')
            lines.append("        client.newCall(builder.build()).execute().use { resp ->")
            lines.append('            if (!resp.isSuccessful) error("HTTP ${resp.code}")')
            lines.append("            return resp.body?.string().orEmpty()")
            lines.append("        }")
            lines.append("    }")
            lines.append("")
        lines.append("}")
        return "\n".join(lines)

    def _swift(self, endpoints: list[dict[str, Any]], base_url: str, class_name: str) -> str:
        lines = [
            "import Foundation",
            "",
            f"final class {class_name} {{",
            "    let baseURL: String",
            "    let token: String?",
            f'    init(baseURL: String = "{base_url}", token: String? = nil) {{',
            '        self.baseURL = baseURL.trimmingCharacters(in: CharacterSet(charactersIn: "/"))',
            "        self.token = token",
            "    }",
            "",
        ]
        for ep in endpoints:
            method = str(ep.get("method") or "GET").upper()
            path = str(ep.get("path") or "/")
            name = self._safe_name(method, path, ep.get("operation_id"))
            lines.append(f"    func {name}(completion: @escaping (Result<Data, Error>) -> Void) {{")
            lines.append(f'        var request = URLRequest(url: URL(string: baseURL + "{path}")!)')
            lines.append(f'        request.httpMethod = "{method}"')
            lines.append('        request.setValue("application/json", forHTTPHeaderField: "Accept")')
            lines.append(
                '        if let token = token { request.setValue("Bearer \\(token)", forHTTPHeaderField: "Authorization") }'
            )
            lines.append("        URLSession.shared.dataTask(with: request) { data, response, error in")
            lines.append("            if let error = error { completion(.failure(error)); return }")
            lines.append("            completion(.success(data ?? Data()))")
            lines.append("        }.resume()")
            lines.append("    }")
            lines.append("")
        lines.append("}")
        return "\n".join(lines)

    def _rust(self, endpoints: list[dict[str, Any]], base_url: str, class_name: str) -> str:
        lines = [
            "use reqwest::header::{ACCEPT, AUTHORIZATION, HeaderMap, HeaderValue};",
            "use reqwest::Client;",
            "",
            f"pub struct {class_name} {{",
            "    base_url: String,",
            "    token: Option<String>,",
            "    client: Client,",
            "}",
            "",
            f"impl {class_name} {{",
            "    pub fn new(base_url: impl Into<String>, token: Option<String>) -> Self {",
            "        let base = base_url.into().trim_end_matches('/').to_string();",
            '        Self { base_url: if base.is_empty() { "'
            + base_url.rstrip("/")
            + '".into() } else { base }, token, client: Client::new() }',
            "    }",
            "",
        ]
        for ep in endpoints:
            method = str(ep.get("method") or "GET").upper()
            path = str(ep.get("path") or "/")
            name = self._safe_name(method, path, ep.get("operation_id"))
            lines.append(f"    pub async fn {name}(&self) -> Result<String, reqwest::Error> {{")
            lines.append("        let mut headers = HeaderMap::new();")
            lines.append('        headers.insert(ACCEPT, HeaderValue::from_static("application/json"));')
            lines.append("        if let Some(token) = &self.token {")
            lines.append(
                '            headers.insert(AUTHORIZATION, HeaderValue::from_str(&format!("Bearer {}", token)).unwrap());'
            )
            lines.append("        }")
            lines.append(
                f'        let resp = self.client.request(reqwest::Method::{method}, format!("{{}}{path}", self.base_url)).headers(headers).send().await?;'
            )
            lines.append("        resp.error_for_status()?.text().await")
            lines.append("    }")
            lines.append("")
        lines.append("}")
        return "\n".join(lines)

    def _filename(self, language: str, class_name: str) -> str:
        mapping = {
            "python": f"{self._snake(class_name)}.py",
            "javascript": f"{self._snake(class_name)}.js",
            "typescript": f"{self._snake(class_name)}.ts",
            "java": f"{class_name}.java",
            "go": f"{self._snake(class_name)}.go",
            "curl": f"{self._snake(class_name)}.sh",
            "csharp": f"{class_name}.cs",
            "php": f"{self._snake(class_name)}.php",
            "ruby": f"{self._snake(class_name)}.rb",
            "kotlin": f"{class_name}.kt",
            "swift": f"{class_name}.swift",
            "rust": f"{self._snake(class_name)}.rs",
        }
        return mapping[language]

    def _snake(self, value: str) -> str:
        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", value)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


codegen_service = CodegenService()
