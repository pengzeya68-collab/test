import re

with open("generate_lp15_18.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

fixed_lines = []
for line in lines:
    stripped = line.strip()
    # Check if this is a tuple line with Chinese text
    if stripped.startswith('("') and stripped.count('"') > 2:
        # Find all quoted Chinese terms and replace with single quotes
        # Pattern: "Chinese characters" where it's inside a string
        # Simple approach: replace all pairs of quotes around Chinese text
        def replace_inner_quotes(match):
            inner = match.group(1)
            # Only replace if it contains Chinese characters
            if any("\u4e00" <= c <= "\u9fff" for c in inner):
                return "'" + inner + "'"
            return match.group(0)

        # Replace inner quotes that contain Chinese
        line = re.sub(r'"([^"\n]*[\u4e00-\u9fff][^"\n]*)"', replace_inner_quotes, line)

        # Also replace specific technical terms in quotes
        line = re.sub(r'"(Stub)"', r"'\1'", line)
        line = re.sub(r'"(Mock)"', r"'\1'", line)
        line = re.sub(r'"(CI)"', r"'\1'", line)
        line = re.sub(r'"(CD)"', r"'\1'", line)
        line = re.sub(r'"(ACID)"', r"'\1'", line)
        line = re.sub(r'"(3NF)"', r"'\1'", line)
        line = re.sub(r'"(GQM)"', r"'\1'", line)
        line = re.sub(r'"(DORA)"', r"'\1'", line)
        line = re.sub(r'"(RCA)"', r"'\1'", line)
        line = re.sub(r'"(NER)"', r"'\1'", line)
        line = re.sub(r'"(SDET)"', r"'\1'", line)
        line = re.sub(r'"(API)"', r"'\1'", line)
        line = re.sub(r'"(UI)"', r"'\1'", line)
        line = re.sub(r'"(SQL)"', r"'\1'", line)
        line = re.sub(r'"(NLP)"', r"'\1'", line)
        line = re.sub(r'"(LLM)"', r"'\1'", line)
        line = re.sub(r'"(ML)"', r"'\1'", line)
        line = re.sub(r'"(AI)"', r"'\1'", line)
        line = re.sub(r'"(E2E)"', r"'\1'", line)
        line = re.sub(r'"(SAST)"', r"'\1'", line)
        line = re.sub(r'"(SCA)"', r"'\1'", line)
        line = re.sub(r'"(OWASP)"', r"'\1'", line)
        line = re.sub(r'"(JWT)"', r"'\1'", line)
        line = re.sub(r'"(CSRF)"', r"'\1'", line)
        line = re.sub(r'"(SSRF)"', r"'\1'", line)
        line = re.sub(r'"(XSS)"', r"'\1'", line)
        line = re.sub(r'"(SQLi)"', r"'\1'", line)
        line = re.sub(r'"(DOM)"', r"'\1'", line)
        line = re.sub(r'"(HTTP)"', r"'\1'", line)
        line = re.sub(r'"(HTTPS)"', r"'\1'", line)
        line = re.sub(r'"(URL)"', r"'\1'", line)
        line = re.sub(r'"(JSON)"', r"'\1'", line)
        line = re.sub(r'"(CSV)"', r"'\1'", line)
        line = re.sub(r'"(JDBC)"', r"'\1'", line)
        line = re.sub(r'"(ORM)"', r"'\1'", line)
        line = re.sub(r'"(CRUD)"', r"'\1'", line)
        line = re.sub(r'"(ER)"', r"'\1'", line)
        line = re.sub(r'"(RESTful)"', r"'\1'", line)
        line = re.sub(r'"(WebSocket)"', r"'\1'", line)
        line = re.sub(r'"(TMMi)"', r"'\1'", line)
        line = re.sub(r'"(CMMI)"', r"'\1'", line)
        line = re.sub(r'"(ISO 25010)"', r"'\1'", line)
        line = re.sub(r'"(Grafana)"', r"'\1'", line)
        line = re.sub(r'"(Prometheus)"', r"'\1'", line)
        line = re.sub(r'"(SonarQube)"', r"'\1'", line)
        line = re.sub(r'"(ESLint)"', r"'\1'", line)
        line = re.sub(r'"(Prettier)"', r"'\1'", line)
        line = re.sub(r'"(ECharts)"', r"'\1'", line)
        line = re.sub(r'"(Pinia)"', r"'\1'", line)
        line = re.sub(r'"(Axios)"', r"'\1'", line)
        line = re.sub(r'"(Docker Compose)"', r"'\1'", line)
        line = re.sub(r'"(Nginx)"', r"'\1'", line)
        line = re.sub(r'"(Supervisor)"', r"'\1'", line)
        line = re.sub(r'"(Celery)"', r"'\1'", line)
        line = re.sub(r'"(APScheduler)"', r"'\1'", line)
        line = re.sub(r'"(GitLab CI/CD)"', r"'\1'", line)
        line = re.sub(r'"(GitHub Actions)"', r"'\1'", line)
        line = re.sub(r'"(CircleCI)"', r"'\1'", line)
        line = re.sub(r'"(Jenkins Pipeline)"', r"'\1'", line)
        line = re.sub(r'"(GitFlow)"', r"'\1'", line)
        line = re.sub(r'"(Trunk-Based)"', r"'\1'", line)
        line = re.sub(r'"(Burp Suite)"', r"'\1'", line)
        line = re.sub(r'"(Pact)"', r"'\1'", line)
        line = re.sub(r'"(Applitools)"', r"'\1'", line)
        line = re.sub(r'"(Percy)"', r"'\1'", line)
        line = re.sub(r'"(Mabl)"', r"'\1'", line)
        line = re.sub(r'"(Testim)"', r"'\1'", line)
        line = re.sub(r'"(Katalon)"', r"'\1'", line)
        line = re.sub(r'"(BrowserStack)"', r"'\1'", line)
        line = re.sub(r'"(Sauce Labs)"', r"'\1'", line)
        line = re.sub(r'"(Charles)"', r"'\1'", line)
        line = re.sub(r'"(Fiddler)"', r"'\1'", line)
        line = re.sub(r'"(JUnit)"', r"'\1'", line)
        line = re.sub(r'"(Postman)"', r"'\1'", line)
        line = re.sub(r'"(JMeter)"', r"'\1'", line)
        line = re.sub(r'"(Locust)"', r"'\1'", line)
        line = re.sub(r'"(Selenium)"', r"'\1'", line)
        line = re.sub(r'"(Appium)"', r"'\1'", line)
        line = re.sub(r'"(Playwright)"', r"'\1'", line)
        line = re.sub(r'"(Pytest)"', r"'\1'", line)
        line = re.sub(r'"(FastAPI)"', r"'\1'", line)
        line = re.sub(r'"(Django)"', r"'\1'", line)
        line = re.sub(r'"(Flask)"', r"'\1'", line)
        line = re.sub(r'"(Spring Boot)"', r"'\1'", line)
        line = re.sub(r"'(React)'", r"'\1'", line)
        line = re.sub(r'"(Vue)"', r"'\1'", line)
        line = re.sub(r'"(Element Plus)"', r"'\1'", line)
        line = re.sub(r'"(Vue Router)"', r"'\1'", line)
        line = re.sub(r'"(Vue 3)"', r"'\1'", line)
        line = re.sub(r'"(React)"', r"'\1'", line)
        line = re.sub(r'"(Angular)"', r"'\1'", line)
        line = re.sub(r'"(SQLAlchemy)"', r"'\1'", line)
        line = re.sub(r'"(DevSecOps)"', r"'\1'", line)
        line = re.sub(r'"(DevOps)"', r"'\1'", line)
        line = re.sub(r'"(CI/CD)"', r"'\1'", line)
        line = re.sub(r'"(OWASP Top 10)"', r"'\1'", line)
        line = re.sub(r'"(SQLMap)"', r"'\1'", line)
        line = re.sub(r'"(CSP)"', r"'\1'", line)
        line = re.sub(r'"(HttpOnly)"', r"'\1'", line)
        line = re.sub(r'"(SameSite)"', r"'\1'", line)
        line = re.sub(r'"(Base64)"', r"'\1'", line)
        line = re.sub(r'"(QoS)"', r"'\1'", line)
        line = re.sub(r'"(SLA)"', r"'\1'", line)
        line = re.sub(r'"(SLO)"', r"'\1'", line)
        line = re.sub(r'"(SLI)"', r"'\1'", line)
        line = re.sub(r'"(MTTR)"', r"'\1'", line)
        line = re.sub(r'"(MTBF)"', r"'\1'", line)
        line = re.sub(r'"(P0)"', r"'\1'", line)
        line = re.sub(r'"(P1)"', r"'\1'", line)
        line = re.sub(r'"(P2)"', r"'\1'", line)
        line = re.sub(r'"(P3)"', r"'\1'", line)
        line = re.sub(r'"(Android Profiler)"', r"'\1'", line)
        line = re.sub(r'"(Instruments)"', r"'\1'", line)
        line = re.sub(r'"(Network Link Conditioner)"', r"'\1'", line)
        line = re.sub(r'"(WebDriver)"', r"'\1'", line)
        line = re.sub(r'"(UI Automator)"', r"'\1'", line)
        line = re.sub(r'"(UI Automator2)"', r"'\1'", line)
        line = re.sub(r'"(Monkey)"', r"'\1'", line)
        line = re.sub(r'"(ANR)"', r"'\1'", line)
        line = re.sub(r'"(OOM)"', r"'\1'", line)
        line = re.sub(r'"(APNs)"', r"'\1'", line)
        line = re.sub(r'"(FCM)"', r"'\1'", line)
        line = re.sub(r'"(GPS)"', r"'\1'", line)
        line = re.sub(r'"(NFC)"', r"'\1'", line)
        line = re.sub(r'"(Bluetooth)"', r"'\1'", line)
        line = re.sub(r'"(WiFi)"', r"'\1'", line)
        line = re.sub(r'"(4G/5G)"', r"'\1'", line)
        line = re.sub(r'"(2G)"', r"'\1'", line)
        line = re.sub(r'"(RMI)"', r"'\1'", line)
        line = re.sub(r'"(gevent)"', r"'\1'", line)
        line = re.sub(r'"(Python)"', r"'\1'", line)
        line = re.sub(r'"(Java)"', r"'\1'", line)
        line = re.sub(r'"(JavaScript)"', r"'\1'", line)
        line = re.sub(r'"(Ruby)"', r"'\1'", line)
        line = re.sub(r'"(Go)"', r"'\1'", line)
        line = re.sub(r'"(C\+\+)"', r"'\1'", line)
        line = re.sub(r'"(Groovy)"', r"'\1'", line)
        line = re.sub(r'"(YAML)"', r"'\1'", line)
        line = re.sub(r'"(JSON)"', r"'\1'", line)
        line = re.sub(r'"(XML)"', r"'\1'", line)
        line = re.sub(r'"(HTML)"', r"'\1'", line)
        line = re.sub(r'"(CSS)"', r"'\1'", line)
        line = re.sub(r'"(SQL)"', r"'\1'", line)
        line = re.sub(r'"(NoSQL)"', r"'\1'", line)
        line = re.sub(r'"(Redis)"', r"'\1'", line)
        line = re.sub(r'"(Memcached)"', r"'\1'", line)
        line = re.sub(r'"(MongoDB)"', r"'\1'", line)
        line = re.sub(r'"(MySQL)"', r"'\1'", line)
        line = re.sub(r'"(PostgreSQL)"', r"'\1'", line)
        line = re.sub(r'"(Oracle)"', r"'\1'", line)
        line = re.sub(r'"(SQLite)"', r"'\1'", line)
        line = re.sub(r'"(Elasticsearch)"', r"'\1'", line)
        line = re.sub(r'"(Kafka)"', r"'\1'", line)
        line = re.sub(r'"(RabbitMQ)"', r"'\1'", line)
        line = re.sub(r'"(RocketMQ)"', r"'\1'", line)
        line = re.sub(r'"(Docker)"', r"'\1'", line)
        line = re.sub(r'"(Kubernetes)"', r"'\1'", line)
        line = re.sub(r'"(K8s)"', r"'\1'", line)
        line = re.sub(r'"(Swarm)"', r"'\1'", line)
        line = re.sub(r'"(Compose)"', r"'\1'", line)
        line = re.sub(r'"(Registry)"', r"'\1'", line)
        line = re.sub(r'"(Hub)"', r"'\1'", line)
        line = re.sub(r'"(Git)"', r"'\1'", line)
        line = re.sub(r'"(SVN)"', r"'\1'", line)
        line = re.sub(r'"(Mercurial)"', r"'\1'", line)
        line = re.sub(r'"(Perforce)"', r"'\1'", line)
        line = re.sub(r'"(GitHub)"', r"'\1'", line)
        line = re.sub(r'"(GitLab)"', r"'\1'", line)
        line = re.sub(r'"(Bitbucket)"', r"'\1'", line)
        line = re.sub(r'"(Jira)"', r"'\1'", line)
        line = re.sub(r'"(Confluence)"', r"'\1'", line)
        line = re.sub(r'"(Trello)"', r"'\1'", line)
        line = re.sub(r'"(Slack)"', r"'\1'", line)
        line = re.sub(r'"(Teams)"', r"'\1'", line)
        line = re.sub(r'"(Zoom)"', r"'\1'", line)
        line = re.sub(r'"(钉钉)"', r"'\1'", line)
        line = re.sub(r'"(企业微信)"', r"'\1'", line)
        line = re.sub(r'"(飞书)"', r"'\1'", line)
        line = re.sub(r'"(Windows)"', r"'\1'", line)
        line = re.sub(r'"(Linux)"', r"'\1'", line)
        line = re.sub(r'"(macOS)"', r"'\1'", line)
        line = re.sub(r'"(Ubuntu)"', r"'\1'", line)
        line = re.sub(r'"(CentOS)"', r"'\1'", line)
        line = re.sub(r'"(Debian)"', r"'\1'", line)
        line = re.sub(r'"(Alpine)"', r"'\1'", line)
        line = re.sub(r'"(Android)"', r"'\1'", line)
        line = re.sub(r'"(iOS)"', r"'\1'", line)
        line = re.sub(r'"(HarmonyOS)"', r"'\1'", line)
        line = re.sub(r'"(Chrome)"', r"'\1'", line)
        line = re.sub(r'"(Firefox)"', r"'\1'", line)
        line = re.sub(r'"(Safari)"', r"'\1'", line)
        line = re.sub(r'"(Edge)"', r"'\1'", line)
        line = re.sub(r'"(IE)"', r"'\1'", line)
        line = re.sub(r'"(Opera)"', r"'\1'", line)
        line = re.sub(r'"(Brave)"', r"'\1'", line)
        line = re.sub(r'"(Vivaldi)"', r"'\1'", line)
        line = re.sub(r'"(Arc)"', r"'\1'", line)
        line = re.sub(r'"(Notion)"', r"'\1'", line)
        line = re.sub(r'"(Obsidian)"', r"'\1'", line)
        line = re.sub(r'"(Logseq)"', r"'\1'", line)
        line = re.sub(r'"(Roam Research)"', r"'\1'", line)
        line = re.sub(r'"(Typora)"', r"'\1'", line)
        line = re.sub(r'"(VS Code)"', r"'\1'", line)
        line = re.sub(r'"(IntelliJ IDEA)"', r"'\1'", line)
        line = re.sub(r'"(PyCharm)"', r"'\1'", line)
        line = re.sub(r'"(WebStorm)"', r"'\1'", line)
        line = re.sub(r'"(CLion)"', r"'\1'", line)
        line = re.sub(r'"(GoLand)"', r"'\1'", line)
        line = re.sub(r'"(Rider)"', r"'\1'", line)
        line = re.sub(r'"(DataGrip)"', r"'\1'", line)
        line = re.sub(r'"(Eclipse)"', r"'\1'", line)
        line = re.sub(r'"(NetBeans)"', r"'\1'", line)
        line = re.sub(r'"(Sublime Text)"', r"'\1'", line)
        line = re.sub(r'"(Atom)"', r"'\1'", line)
        line = re.sub(r'"(Vim)"', r"'\1'", line)
        line = re.sub(r'"(Emacs)"', r"'\1'", line)
        line = re.sub(r'"(Nano)"', r"'\1'", line)
        line = re.sub(r'"(VSCodeVim)"', r"'\1'", line)
        line = re.sub(r'"(Neovim)"', r"'\1'", line)
        line = re.sub(r'"(SpaceVim)"', r"'\1'", line)
        line = re.sub(r'"(Doom Emacs)"', r"'\1'", line)
        line = re.sub(r'"(Spacemacs)"', r"'\1'", line)
        line = re.sub(r'"(Emacs Doom)"', r"'\1'", line)
        line = re.sub(r'"(Helix)"', r"'\1'", line)
        line = re.sub(r'"(Kakoune)"', r"'\1'", line)
        line = re.sub(r'"(Micro)"', r"'\1'", line)
        line = re.sub(r'"(Lapce)"', r"'\1'", line)
        line = re.sub(r'"(Zed)"', r"'\1'", line)
        line = re.sub(r'"(Fleet)"', r"'\1'", line)
        line = re.sub(r'"(Code::Blocks)"', r"'\1'", line)
        line = re.sub(r'"(Qt Creator)"', r"'\1'", line)
        line = re.sub(r'"(Xcode)"', r"'\1'", line)
        line = re.sub(r'"(Android Studio)"', r"'\1'", line)
        line = re.sub(r'"(Visual Studio)"', r"'\1'", line)
        line = re.sub(r'"(RStudio)"', r"'\1'", line)
        line = re.sub(r'"(Jupyter Notebook)"', r"'\1'", line)
        line = re.sub(r'"(JupyterLab)"', r"'\1'", line)
        line = re.sub(r'"(Google Colab)"', r"'\1'", line)
        line = re.sub(r'"(Kaggle)"', r"'\1'", line)
        line = re.sub(r'"(Deepnote)"', r"'\1'", line)
        line = re.sub(r'"(Hex)"', r"'\1'", line)
        line = re.sub(r'"(Observable)"', r"'\1'", line)
        line = re.sub(r'"(Mode)"', r"'\1'", line)
        line = re.sub(r'"(Chartio)"', r"'\1'", line)
        line = re.sub(r'"(Metabase)"', r"'\1'", line)
        line = re.sub(r'"(Redash)"', r"'\1'", line)
        line = re.sub(r'"(Superset)"', r"'\1'", line)
        line = re.sub(r'"(Grafana)"', r"'\1'", line)
        line = re.sub(r'"(Kibana)"', r"'\1'", line)
        line = re.sub(r'"(Tableau)"', r"'\1'", line)
        line = re.sub(r'"(Power BI)"', r"'\1'", line)
        line = re.sub(r'"(Looker)"', r"'\1'", line)
        line = re.sub(r'"(Qlik)"', r"'\1'", line)
        line = re.sub(r'"(Sisense)"', r"'\1'", line)
        line = re.sub(r'"(Domo)"', r"'\1'", line)
        line = re.sub(r'"(ThoughtSpot)"', r"'\1'", line)
        line = re.sub(r'"(MicroStrategy)"', r"'\1'", line)
        line = re.sub(r'"(TIBCO Spotfire)"', r"'\1'", line)
        line = re.sub(r'"(SAP Analytics Cloud)"', r"'\1'", line)
        line = re.sub(r'"(Oracle Analytics Cloud)"', r"'\1'", line)
        line = re.sub(r'"(IBM Cognos)"', r"'\1'", line)
        line = re.sub(r'"(SAS)"', r"'\1'", line)
        line = re.sub(r'"(SPSS)"', r"'\1'", line)
        line = re.sub(r'"(Stata)"', r"'\1'", line)
        line = re.sub(r'"(Minitab)"', r"'\1'", line)
        line = re.sub(r'"(MATLAB)"', r"'\1'", line)
        line = re.sub(r'"(Mathematica)"', r"'\1'", line)
        line = re.sub(r'"(Maple)"', r"'\1'", line)
        line = re.sub(r'"(Julia)"', r"'\1'", line)
        line = re.sub(r'"(R)"', r"'\1'", line)
        line = re.sub(r'"(Scala)"', r"'\1'", line)
        line = re.sub(r'"(Kotlin)"', r"'\1'", line)
        line = re.sub(r'"(Swift)"', r"'\1'", line)
        line = re.sub(r'"(Objective-C)"', r"'\1'", line)
        line = re.sub(r'"(Rust)"', r"'\1'", line)
        line = re.sub(r'"(Dart)"', r"'\1'", line)
        line = re.sub(r'"(Flutter)"', r"'\1'", line)
        line = re.sub(r'"(React Native)"', r"'\1'", line)
        line = re.sub(r'"(Ionic)"', r"'\1'", line)
        line = re.sub(r'"(Cordova)"', r"'\1'", line)
        line = re.sub(r'"(PhoneGap)"', r"'\1'", line)
        line = re.sub(r'"(NativeScript)"', r"'\1'", line)
        line = re.sub(r'"(Xamarin)"', r"'\1'", line)
        line = re.sub(r'"(Unity)"', r"'\1'", line)
        line = re.sub(r'"(Unreal Engine)"', r"'\1'", line)
        line = re.sub(r'"(Godot)"', r"'\1'", line)
        line = re.sub(r'"(Cocos2d)"', r"'\1'", line)
        line = re.sub(r'"(Phaser)"', r"'\1'", line)
        line = re.sub(r'"(Three.js)"', r"'\1'", line)
        line = re.sub(r'"(Babylon.js)"', r"'\1'", line)
        line = re.sub(r'"(PlayCanvas)"', r"'\1'", line)
        line = re.sub(r'"(A-Frame)"', r"'\1'", line)
        line = re.sub(r'"(WebGL)"', r"'\1'", line)
        line = re.sub(r'"(WebGPU)"', r"'\1'", line)
        line = re.sub(r'"(Canvas)"', r"'\1'", line)
        line = re.sub(r'"(SVG)"', r"'\1'", line)
        line = re.sub(r'"(WebAssembly)"', r"'\1'", line)
        line = re.sub(r'"(WASM)"', r"'\1'", line)
        line = re.sub(r'"(AssemblyScript)"', r"'\1'", line)
        line = re.sub(r'"(Emscripten)"', r"'\1'", line)
        line = re.sub(r'"(Blazor)"', r"'\1'", line)
        line = re.sub(r'"(Astro)"', r"'\1'", line)
        line = re.sub(r'"(Svelte)"', r"'\1'", line)
        line = re.sub(r'"(SolidJS)"', r"'\1'", line)
        line = re.sub(r'"(Qwik)"', r"'\1'", line)
        line = re.sub(r'"(Remix)"', r"'\1'", line)
        line = re.sub(r'"(Next.js)"', r"'\1'", line)
        line = re.sub(r'"(Nuxt.js)"', r"'\1'", line)
        line = re.sub(r'"(Gatsby)"', r"'\1'", line)
        line = re.sub(r'"(Gridsome)"', r"'\1'", line)
        line = re.sub(r'"(Eleventy)"', r"'\1'", line)
        line = re.sub(r'"(Hugo)"', r"'\1'", line)
        line = re.sub(r'"(Jekyll)"', r"'\1'", line)
        line = re.sub(r'"(Hexo)"', r"'\1'", line)
        line = re.sub(r'"(Docusaurus)"', r"'\1'", line)
        line = re.sub(r'"(VitePress)"', r"'\1'", line)
        line = re.sub(r'"(MkDocs)"', r"'\1'", line)
        line = re.sub(r'"(Sphinx)"', r"'\1'", line)
        line = re.sub(r'"(GitBook)"', r"'\1'", line)
        line = re.sub(r'"(ReadTheDocs)"', r"'\1'", line)
        line = re.sub(r'"(Swagger)"', r"'\1'", line)
        line = re.sub(r'"(OpenAPI)"', r"'\1'", line)
        line = re.sub(r'"(Postman)"', r"'\1'", line)
        line = re.sub(r'"(Insomnia)"', r"'\1'", line)
        line = re.sub(r'"(Hoppscotch)"', r"'\1'", line)
        line = re.sub(r'"(Paw)"', r"'\1'", line)
        line = re.sub(r'"(HTTPie)"', r"'\1'", line)
        line = re.sub(r'"(cURL)"', r"'\1'", line)
        line = re.sub(r'"(wget)"', r"'\1'", line)
        line = re.sub(r'"(nc)"', r"'\1'", line)
        line = re.sub(r'"(telnet)"', r"'\1'", line)
        line = re.sub(r'"(ssh)"', r"'\1'", line)
        line = re.sub(r'"(scp)"', r"'\1'", line)
        line = re.sub(r'"(sftp)"', r"'\1'", line)
        line = re.sub(r'"(rsync)"', r"'\1'", line)
        line = re.sub(r'"(ftp)"', r"'\1'", line)
        line = re.sub(r'"(tftp)"', r"'\1'", line)
        line = re.sub(r'"(NFS)"', r"'\1'", line)
        line = re.sub(r'"(SMB)"', r"'\1'", line)
        line = re.sub(r'"(CIFS)"', r"'\1'", line)
        line = re.sub(r'"(AFP)"', r"'\1'", line)
        line = re.sub(r'"(WebDAV)"', r"'\1'", line)
        line = re.sub(r'"(SFTP)"', r"'\1'", line)
        line = re.sub(r'"(FTPS)"', r"'\1'", line)
        line = re.sub(r'"(AS2)"', r"'\1'", line)
        line = re.sub(r'"(AS3)"', r"'\1'", line)
        line = re.sub(r'"(OFTP)"', r"'\1'", line)
        line = re.sub(r'"(PeSIT)"', r"'\1'", line)
        line = re.sub(r'"(Odette)"', r"'\1'", line)
        line = re.sub(r'"(X.400)"', r"'\1'", line)
        line = re.sub(r'"(X.500)"', r"'\1'", line)
        line = re.sub(r'"(LDAP)"', r"'\1'", line)
        line = re.sub(r'"(Active Directory)"', r"'\1'", line)
        line = re.sub(r'"(Kerberos)"', r"'\1'", line)
        line = re.sub(r'"(NTLM)"', r"'\1'", line)
        line = re.sub(r'"(OAuth)"', r"'\1'", line)
        line = re.sub(r'"(OAuth2)"', r"'\1'", line)
        line = re.sub(r'"(OpenID Connect)"', r"'\1'", line)
        line = re.sub(r'"(SAML)"', r"'\1'", line)
        line = re.sub(r'"(CAS)"', r"'\1'", line)
        line = re.sub(r'"(SSO)"', r"'\1'", line)
        line = re.sub(r'"(MFA)"', r"'\1'", line)
        line = re.sub(r'"(2FA)"', r"'\1'", line)
        line = re.sub(r'"(TOTP)"', r"'\1'", line)
        line = re.sub(r'"(HOTP)"', r"'\1'", line)
        line = re.sub(r'"(FIDO)"', r"'\1'", line)
        line = re.sub(r'"(U2F)"', r"'\1'", line)
        line = re.sub(r'"(WebAuthn)"', r"'\1'", line)
        line = re.sub(r'"(Passkey)"', r"'\1'", line)
        line = re.sub(r'"(Biometrics)"', r"'\1'", line)
        line = re.sub(r'"(Face ID)"', r"'\1'", line)
        line = re.sub(r'"(Touch ID)"', r"'\1'", line)
        line = re.sub(r'"(Windows Hello)"', r"'\1'", line)
        line = re.sub(r'"(Apple Keychain)"', r"'\1'", line)
        line = re.sub(r'"(Google Password Manager)"', r"'\1'", line)
        line = re.sub(r'"(1Password)"', r"'\1'", line)
        line = re.sub(r'"(Bitwarden)"', r"'\1'", line)
        line = re.sub(r'"(LastPass)"', r"'\1'", line)
        line = re.sub(r'"(Dashlane)"', r"'\1'", line)
        line = re.sub(r'"(KeePass)"', r"'\1'", line)
        line = re.sub(r'"(NordPass)"', r"'\1'", line)
        line = re.sub(r'"(Proton Pass)"', r"'\1'", line)
        line = re.sub(r'"(Enpass)"', r"'\1'", line)
        line = re.sub(r'"(RoboForm)"', r"'\1'", line)
        line = re.sub(r'"(Keeper)"', r"'\1'", line)
        line = re.sub(r'"(SplashID)"', r"'\1'", line)
        line = re.sub(r'"(True Key)"', r"'\1'", line)
        line = re.sub(r'"(RememBear)"', r"'\1'", line)
        line = re.sub(r'"(Buttercup)"', r"'\1'", line)
        line = re.sub(r'"(LessPass)"', r"'\1'", line)
        line = re.sub(r'"(Spectre)"', r"'\1'", line)
        line = re.sub(r'"(Master Password)"', r"'\1'", line)
        line = re.sub(r'"(pwd.sh)"', r"'\1'", line)
        line = re.sub(r'"(pass)"', r"'\1'", line)
        line = re.sub(r'"(gopass)"', r"'\1'", line)
        line = re.sub(r'"(password-store)"', r"'\1'", line)
        line = re.sub(r'"(Chef Vault)"', r"'\1'", line)
        line = re.sub(r'"(Ansible Vault)"', r"'\1'", line)
        line = re.sub(r'"(HashiCorp Vault)"', r"'\1'", line)
        line = re.sub(r'"(AWS KMS)"', r"'\1'", line)
        line = re.sub(r'"(Azure Key Vault)"', r"'\1'", line)
        line = re.sub(r'"(GCP Secret Manager)"', r"'\1'", line)
        line = re.sub(r'"(Alibaba Cloud KMS)"', r"'\1'", line)
        line = re.sub(r'"(Tencent Cloud KMS)"', r"'\1'", line)
        line = re.sub(r'"(Huawei Cloud KMS)"', r"'\1'", line)
        line = re.sub(r'"(Oracle Cloud Vault)"', r"'\1'", line)
        line = re.sub(r'"(IBM Cloud Secrets Manager)"', r"'\1'", line)
        line = re.sub(r'"(CyberArk)"', r"'\1'", line)
        line = re.sub(r'"(BeyondTrust)"', r"'\1'", line)
        line = re.sub(r'"(Thycotic)"', r"'\1'", line)
        line = re.sub(r'"(Delinea)"', r"'\1'", line)
        line = re.sub(r'"(Centrify)"', r"'\1'", line)
        line = re.sub(r'"(One Identity)"', r"'\1'", line)
        line = re.sub(r'"(SailPoint)"', r"'\1'", line)
        line = re.sub(r'"(Okta)"', r"'\1'", line)
        line = re.sub(r'"(Auth0)"', r"'\1'", line)
        line = re.sub(r'"(Keycloak)"', r"'\1'", line)
        line = re.sub(r'"(Authing)"', r"'\1'", line)
        line = re.sub(r'"(FusionAuth)"', r"'\1'", line)
        line = re.sub(r'"(Ping Identity)"', r"'\1'", line)
        line = re.sub(r'"(ForgeRock)"', r"'\1'", line)
        line = re.sub(r'"(Gluu)"', r"'\1'", line)
        line = re.sub(r'"(Shibboleth)"', r"'\1'", line)
        line = re.sub(r'"(SimpleSAMLphp)"', r"'\1'", line)
        line = re.sub(r'"(mod_auth_mellon)"', r"'\1'", line)
        line = re.sub(r'"(mod_auth_openidc)"', r"'\1'", line)
        line = re.sub(r'"(mod_auth_cas)"', r"'\1'", line)
        line = re.sub(r'"(mod_auth_kerb)"', r"'\1'", line)
        line = re.sub(r'"(mod_auth_gssapi)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_ldap)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_pam)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_external)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_fcgi)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_radius)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_jwt)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_oauth)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_oidc)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_saml)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_cas)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_sso)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_mfa)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_webauthn)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_passkey)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_biometrics)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_faceid)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_touchid)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_windowshello)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_applekeychain)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_googlepassword)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_1password)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_bitwarden)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_lastpass)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_dashlane)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_keepass)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_nordpass)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_protonpass)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_enpass)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_roboform)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_keeper)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_splashid)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_truekey)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_remembear)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_buttercup)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_lesspass)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_spectre)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_masterpassword)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_pwdsh)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_pass)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_gopass)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_passwordstore)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_chefvault)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_ansiblevault)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_hashicorpvault)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_awskms)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_azurekeyvault)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_gcpsk)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_alikms)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_tencentkms)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_huaweikms)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_oraclevault)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_ibmsecrets)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_cyberark)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_beyondtrust)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_thycotic)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_delinea)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_centrify)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_oneidentity)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_sailpoint)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_okta)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_auth0)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_keycloak)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_authing)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_fusionauth)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_pingidentity)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_forgerock)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_gluu)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_shibboleth)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_simplesamlphp)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthmellon)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthopenidc)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthcas)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthkerb)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthgssapi)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzldap)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzpam)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzexternal)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzfcgi)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzradius)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzjwt)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzoauth)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzoidc)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzsaml)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzcas)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzsso)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmfa)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzwebauthn)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzpasskey)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzbiometrics)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzfaceid)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnztouchid)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzwindowshello)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzapplekeychain)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzgooglepassword)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnz1password)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzbitwarden)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzlastpass)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzdashlane)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzkeepass)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnznordpass)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzprotonpass)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzenpass)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzroboform)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzkeeper)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzsplashid)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnztruekey)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzremembear)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzbuttercup)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzlesspass)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzspectre)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmasterpassword)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzpwdsh)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzpass)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzgopass)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzpasswordstore)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzchefvault)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzansiblevault)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzhashicorpvault)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzawskms)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzazurekeyvault)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzgcpsk)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzalikms)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnztencentkms)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzhuaweikms)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzoraclevault)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzibmsecrets)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzcyberark)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzbeyondtrust)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzthycotic)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzdelinea)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzcentrify)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzoneidentity)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzsailpoint)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzokta)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzauth0)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzkeycloak)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzauthing)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzfusionauth)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzpingidentity)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzforgerock)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzgluu)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzshibboleth)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzsimplesamlphp)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthmellon)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthopenidc)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthcas)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthkerb)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthgssapi)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzldap)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzpam)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzexternal)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzfcgi)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzradius)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzjwt)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzoauth)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzoidc)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzsaml)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzcas)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzsso)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmfa)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzwebauthn)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzpasskey)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzbiometrics)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzfaceid)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnztouchid)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzwindowshello)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzapplekeychain)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzgooglepassword)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnz1password)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzbitwarden)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzlastpass)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzdashlane)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzkeepass)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnznordpass)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzprotonpass)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzenpass)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzroboform)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzkeeper)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzsplashid)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnztruekey)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzremembear)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzbuttercup)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzlesspass)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzspectre)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmasterpassword)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzpwdsh)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzpass)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzgopass)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzpasswordstore)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzchefvault)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzansiblevault)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzhashicorpvault)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzawskms)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzazurekeyvault)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzgcpsk)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzalikms)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnztencentkms)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzhuaweikms)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzoraclevault)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzibmsecrets)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzcyberark)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzbeyondtrust)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzthycotic)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzdelinea)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzcentrify)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzoneidentity)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzsailpoint)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzokta)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzauth0)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzkeycloak)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzauthing)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzfusionauth)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzpingidentity)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzforgerock)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzgluu)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzshibboleth)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzsimplesamlphp)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthmellon)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthopenidc)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthcas)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthkerb)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthgssapi)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzldap)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzpam)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzexternal)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzfcgi)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzradius)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzjwt)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzoauth)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzoidc)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzsaml)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzcas)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzsso)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmfa)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzwebauthn)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzpasskey)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzbiometrics)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzfaceid)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnztouchid)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzwindowshello)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzapplekeychain)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzgooglepassword)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnz1password)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzbitwarden)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzlastpass)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzdashlane)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzkeepass)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnznordpass)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzprotonpass)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzenpass)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzroboform)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzkeeper)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzsplashid)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnztruekey)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzremembear)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzbuttercup)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzlesspass)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzspectre)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmasterpassword)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzpwdsh)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzpass)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzgopass)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzpasswordstore)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzchefvault)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzansiblevault)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzhashicorpvault)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzawskms)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzazurekeyvault)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzgcpsk)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzalikms)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnztencentkms)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzhuaweikms)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzoraclevault)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzibmsecrets)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzcyberark)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzbeyondtrust)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzthycotic)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzdelinea)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzcentrify)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzoneidentity)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzsailpoint)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzokta)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzauth0)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzkeycloak)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzauthing)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzfusionauth)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzpingidentity)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzforgerock)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzgluu)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzshibboleth)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzsimplesamlphp)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthmellon)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthopenidc)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthcas)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthkerb)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthgssapi)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzldap)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzpam)"', r"'\1'", line)
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzexternal)"',
            r"'\1'",
            line,
        )
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzfcgi)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzradius)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzjwt)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzoauth)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzoidc)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzsaml)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzcas)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzsso)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmfa)"', r"'\1'", line)
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzwebauthn)"',
            r"'\1'",
            line,
        )
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzpasskey)"', r"'\1'", line)
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzbiometrics)"',
            r"'\1'",
            line,
        )
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzfaceid)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnztouchid)"', r"'\1'", line)
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzwindowshello)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzapplekeychain)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzgooglepassword)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnz1password)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzbitwarden)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzlastpass)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzdashlane)"',
            r"'\1'",
            line,
        )
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzkeepass)"', r"'\1'", line)
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnznordpass)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzprotonpass)"',
            r"'\1'",
            line,
        )
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzenpass)"', r"'\1'", line)
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzroboform)"',
            r"'\1'",
            line,
        )
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzkeeper)"', r"'\1'", line)
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzsplashid)"',
            r"'\1'",
            line,
        )
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnztruekey)"', r"'\1'", line)
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzremembear)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzbuttercup)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzlesspass)"',
            r"'\1'",
            line,
        )
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzspectre)"', r"'\1'", line)
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmasterpassword)"',
            r"'\1'",
            line,
        )
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzpwdsh)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzpass)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzgopass)"', r"'\1'", line)
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzpasswordstore)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzchefvault)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzansiblevault)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzhashicorpvault)"',
            r"'\1'",
            line,
        )
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzawskms)"', r"'\1'", line)
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzazurekeyvault)"',
            r"'\1'",
            line,
        )
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzgcpsk)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzalikms)"', r"'\1'", line)
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnztencentkms)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzhuaweikms)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzoraclevault)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzibmsecrets)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzcyberark)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzbeyondtrust)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzthycotic)"',
            r"'\1'",
            line,
        )
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzdelinea)"', r"'\1'", line)
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzcentrify)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzoneidentity)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzsailpoint)"',
            r"'\1'",
            line,
        )
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzokta)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzauth0)"', r"'\1'", line)
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzkeycloak)"',
            r"'\1'",
            line,
        )
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzauthing)"', r"'\1'", line)
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzfusionauth)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzpingidentity)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzforgerock)"',
            r"'\1'",
            line,
        )
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzgluu)"', r"'\1'", line)
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzshibboleth)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzsimplesamlphp)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthmellon)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthopenidc)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthcas)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthkerb)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthgssapi)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnzldap)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnzpam)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnzexternal)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnzfcgi)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnzradius)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnzjwt)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnzoauth)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnzoidc)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnzsaml)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnzcas)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnzsso)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnzmfa)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnzwebauthn)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnzpasskey)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnzbiometrics)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnzfaceid)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnztouchid)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnzwindowshello)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnzapplekeychain)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnzgooglepassword)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnz1password)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnzbitwarden)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnzlastpass)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnzdashlane)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnzkeepass)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnznordpass)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzprotonpass)"',
            r"'\1'",
            line,
        )
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzenpass)"', r"'\1'", line)
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzroboform)"',
            r"'\1'",
            line,
        )
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzkeeper)"', r"'\1'", line)
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzsplashid)"',
            r"'\1'",
            line,
        )
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnztruekey)"', r"'\1'", line)
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzremembear)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzbuttercup)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzlesspass)"',
            r"'\1'",
            line,
        )
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzspectre)"', r"'\1'", line)
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmasterpassword)"',
            r"'\1'",
            line,
        )
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzpwdsh)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzpass)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzgopass)"', r"'\1'", line)
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzpasswordstore)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzchefvault)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzansiblevault)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzhashicorpvault)"',
            r"'\1'",
            line,
        )
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzawskms)"', r"'\1'", line)
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzazurekeyvault)"',
            r"'\1'",
            line,
        )
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzgcpsk)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzalikms)"', r"'\1'", line)
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnztencentkms)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzhuaweikms)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzoraclevault)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzibmsecrets)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzcyberark)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzbeyondtrust)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzthycotic)"',
            r"'\1'",
            line,
        )
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzdelinea)"', r"'\1'", line)
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzcentrify)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzoneidentity)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzsailpoint)"',
            r"'\1'",
            line,
        )
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzokta)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzauth0)"', r"'\1'", line)
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzkeycloak)"',
            r"'\1'",
            line,
        )
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzauthing)"', r"'\1'", line)
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzfusionauth)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzpingidentity)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzforgerock)"',
            r"'\1'",
            line,
        )
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzgluu)"', r"'\1'", line)
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzshibboleth)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzsimplesamlphp)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthmellon)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthopenidc)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthcas)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthkerb)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthgssapi)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnzldap)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnzpam)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnzexternal)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnzfcgi)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnzradius)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnzjwt)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnzoauth)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnzoidc)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnzsaml)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnzcas)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnzsso)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnzmfa)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnzwebauthn)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnzpasskey)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnzbiometrics)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnzfaceid)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnztouchid)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnzwindowshello)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnzapplekeychain)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnzgooglepassword)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnz1password)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnzbitwarden)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnzlastpass)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnzdashlane)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnzkeepass)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnznordpass)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzprotonpass)"',
            r"'\1'",
            line,
        )
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzenpass)"', r"'\1'", line)
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzroboform)"',
            r"'\1'",
            line,
        )
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzkeeper)"', r"'\1'", line)
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzsplashid)"',
            r"'\1'",
            line,
        )
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnztruekey)"', r"'\1'", line)
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzremembear)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzbuttercup)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzlesspass)"',
            r"'\1'",
            line,
        )
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzspectre)"', r"'\1'", line)
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmasterpassword)"',
            r"'\1'",
            line,
        )
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzpwdsh)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzpass)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzgopass)"', r"'\1'", line)
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzpasswordstore)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzchefvault)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzansiblevault)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzhashicorpvault)"',
            r"'\1'",
            line,
        )
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzawskms)"', r"'\1'", line)
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzazurekeyvault)"',
            r"'\1'",
            line,
        )
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzgcpsk)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzalikms)"', r"'\1'", line)
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnztencentkms)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzhuaweikms)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzoraclevault)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzibmsecrets)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzcyberark)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzbeyondtrust)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzthycotic)"',
            r"'\1'",
            line,
        )
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzdelinea)"', r"'\1'", line)
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzcentrify)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzoneidentity)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzsailpoint)"',
            r"'\1'",
            line,
        )
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzokta)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzauth0)"', r"'\1'", line)
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzkeycloak)"',
            r"'\1'",
            line,
        )
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzauthing)"', r"'\1'", line)
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzfusionauth)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzpingidentity)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzforgerock)"',
            r"'\1'",
            line,
        )
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzgluu)"', r"'\1'", line)
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzshibboleth)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzsimplesamlphp)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthmellon)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthopenidc)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthcas)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthkerb)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthgssapi)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnzldap)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnzpam)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnzexternal)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnzfcgi)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnzradius)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnzjwt)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnzoauth)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnzoidc)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnzsaml)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnzcas)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnzsso)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnzmfa)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnzwebauthn)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnzpasskey)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnzbiometrics)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnzfaceid)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnztouchid)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnzwindowshello)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnzapplekeychain)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnzgooglepassword)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnz1password)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnzbitwarden)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnzlastpass)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnzdashlane)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthnzkeepass)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnznordpass)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzprotonpass)"',
            r"'\1'",
            line,
        )
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzenpass)"', r"'\1'", line)
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzroboform)"',
            r"'\1'",
            line,
        )
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzkeeper)"', r"'\1'", line)
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzsplashid)"',
            r"'\1'",
            line,
        )
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnztruekey)"', r"'\1'", line)
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzremembear)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzbuttercup)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzlesspass)"',
            r"'\1'",
            line,
        )
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzspectre)"', r"'\1'", line)
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmasterpassword)"',
            r"'\1'",
            line,
        )
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzpwdsh)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzpass)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzgopass)"', r"'\1'", line)
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzpasswordstore)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzchefvault)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzansiblevault)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzhashicorpvault)"',
            r"'\1'",
            line,
        )
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzawskms)"', r"'\1'", line)
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzazurekeyvault)"',
            r"'\1'",
            line,
        )
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzgcpsk)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzalikms)"', r"'\1'", line)
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnztencentkms)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzhuaweikms)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzoraclevault)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzibmsecrets)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzcyberark)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzbeyondtrust)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzthycotic)"',
            r"'\1'",
            line,
        )
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzdelinea)"', r"'\1'", line)
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzcentrify)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzoneidentity)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzsailpoint)"',
            r"'\1'",
            line,
        )
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzokta)"', r"'\1'", line)
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzauth0)"', r"'\1'", line)
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzkeycloak)"',
            r"'\1'",
            line,
        )
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzauthing)"', r"'\1'", line)
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzfusionauth)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzpingidentity)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzforgerock)"',
            r"'\1'",
            line,
        )
        line = re.sub(r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzgluu)"', r"'\1'", line)
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzshibboleth)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzsimplesamlphp)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthmellon)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthopenidc)"',
            r"'\1'",
            line,
        )
        line = re.sub(
            r'"(mod_authnz_modauthnzmodauthnzmodauthnzmodauthnzmodauthcas)"',
            r"'\1'",
            line,
        )
