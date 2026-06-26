# companies.py — job board registry
#
# VERIFIED  : ATS board URL is known. Fetched directly every run.
# DISCOVER  : Bare name only. The resolver probes GH/Lever/Ashby slug
#             candidates and caches whatever resolves. Misses are silent.
# WORKDAY   : Needs host + tenant + site path; add only when confirmed.
#
# To add a company: drop it into DISCOVER (safest) or VERIFIED if you know
# the board URL. Everything else — filtering, dedup, scoring — is automatic.

# ── VERIFIED ──────────────────────────────────────────────────────────────────

VERIFIED = [

    # ── Greenhouse ────────────────────────────────────────────────────────────

    # Big / late-stage
    ("Databricks",          "https://boards.greenhouse.io/databricks"),
    ("Stripe",              "https://boards.greenhouse.io/stripe"),
    ("Figma",               "https://boards.greenhouse.io/figma"),
    ("Airbnb",              "https://boards.greenhouse.io/airbnb"),
    ("Lyft",                "https://boards.greenhouse.io/lyft"),
    ("Pinterest",           "https://boards.greenhouse.io/pinterest"),
    ("Instacart",           "https://boards.greenhouse.io/instacart"),
    ("Reddit",              "https://job-boards.greenhouse.io/reddit"),
    ("Affirm",              "https://job-boards.greenhouse.io/affirm"),
    ("Chime",               "https://boards.greenhouse.io/chime"),
    ("Brex",                "https://boards.greenhouse.io/brex"),
    ("Gusto",               "https://boards.greenhouse.io/gusto"),
    ("Samsara",             "https://boards.greenhouse.io/samsara"),
    ("Scale AI",            "https://job-boards.greenhouse.io/scaleai"),
    ("Anthropic",           "https://boards.greenhouse.io/anthropic"),
    ("DoorDash",            "https://boards.greenhouse.io/doordashusa"),
    ("Coinbase",            "https://boards.greenhouse.io/coinbase"),
    ("Robinhood",           "https://boards.greenhouse.io/robinhood"),
    ("Dropbox",             "https://boards.greenhouse.io/dropbox"),
    ("Cloudflare",          "https://boards.greenhouse.io/cloudflare"),
    ("Datadog",             "https://boards.greenhouse.io/datadog"),
    ("MongoDB",             "https://boards.greenhouse.io/mongodb"),
    ("SoFi",                "https://boards.greenhouse.io/sofi"),

    # Growth / mid-size
    ("Discord",             "https://boards.greenhouse.io/discord"),
    ("Duolingo",            "https://boards.greenhouse.io/duolingo"),
    ("Nextdoor",            "https://boards.greenhouse.io/nextdoor"),
    ("Faire",               "https://boards.greenhouse.io/faire"),
    ("Flexport",            "https://boards.greenhouse.io/flexport"),
    ("Asana",               "https://boards.greenhouse.io/asana"),
    ("Airtable",            "https://boards.greenhouse.io/airtable"),
    ("Lattice",             "https://boards.greenhouse.io/lattice"),
    ("Gong",                "https://boards.greenhouse.io/gongio"),
    ("Checkr",              "https://boards.greenhouse.io/checkr"),
    ("Verkada",             "https://boards.greenhouse.io/verkada"),
    ("Webflow",             "https://boards.greenhouse.io/webflow"),
    ("Anduril",             "https://boards.greenhouse.io/andurilindustries"),
    ("Nuro",                "https://boards.greenhouse.io/nuro"),
    ("Navan",               "https://boards.greenhouse.io/tripactions"),
    ("Komodo Health",       "https://boards.greenhouse.io/komodohealth"),
    ("Cockroach Labs",      "https://boards.greenhouse.io/cockroachlabs"),
    ("Marqeta",             "https://boards.greenhouse.io/marqeta"),
    ("Mixpanel",            "https://boards.greenhouse.io/mixpanel"),
    ("Amplitude",           "https://boards.greenhouse.io/amplitude"),
    ("Intercom",            "https://boards.greenhouse.io/intercom"),
    ("Box",                 "https://boards.greenhouse.io/boxinc"),
    ("Okta",                "https://boards.greenhouse.io/okta"),
    ("Twilio",              "https://boards.greenhouse.io/twilio"),
    ("HubSpot",             "https://boards.greenhouse.io/hubspot"),
    ("GitLab",              "https://boards.greenhouse.io/gitlab"),
    ("Elastic",             "https://boards.greenhouse.io/elastic"),
    ("Modern Health",       "https://boards.greenhouse.io/modernhealth"),
    ("Coursera",            "https://boards.greenhouse.io/coursera"),
    ("Udemy",               "https://boards.greenhouse.io/udemy"),
    ("Smartsheet",          "https://boards.greenhouse.io/smartsheet"),
    ("Salesloft",           "https://boards.greenhouse.io/salesloft"),
    ("Carta",               "https://boards.greenhouse.io/carta"),
    ("Fivetran",            "https://boards.greenhouse.io/fivetran"),
    ("Starburst",           "https://boards.greenhouse.io/starburst"),
    ("ClickHouse",          "https://boards.greenhouse.io/clickhouse"),
    ("Cribl",               "https://boards.greenhouse.io/cribl"),
    # Corrected from wrong Lever slug → GH
    ("Mercury",             "https://boards.greenhouse.io/mercury"),
    ("Cresta",              "https://boards.greenhouse.io/cresta"),
    ("Netlify",             "https://boards.greenhouse.io/netlify"),
    ("Hex",                 "https://boards.greenhouse.io/hextechnologies"),
    ("Glean",               "https://boards.greenhouse.io/gleanwork"),

    # ── Lever ─────────────────────────────────────────────────────────────────

    ("Plaid",               "https://jobs.lever.co/plaid"),
    ("Palantir",            "https://jobs.lever.co/palantir"),
    ("Zoox",                "https://jobs.lever.co/zoox"),
    ("Alloy",               "https://jobs.lever.co/alloy"),
    ("AngelList",           "https://jobs.lever.co/angellist"),
    # Corrected from wrong GH slug → Lever
    ("Clari",               "https://jobs.lever.co/clari"),
    ("Outreach",            "https://jobs.lever.co/outreach"),
    ("Color Health",        "https://jobs.lever.co/color"),

    # ── Ashby ─────────────────────────────────────────────────────────────────

    ("OpenAI",              "https://jobs.ashbyhq.com/openai"),
    ("Perplexity",          "https://jobs.ashbyhq.com/perplexity"),
    ("Ramp",                "https://jobs.ashbyhq.com/ramp"),
    ("Notion",              "https://jobs.ashbyhq.com/notion"),
    ("Harvey",              "https://jobs.ashbyhq.com/harvey"),
    ("Sierra",              "https://jobs.ashbyhq.com/sierra"),
    ("Cursor",              "https://jobs.ashbyhq.com/cursor"),
    ("Supabase",            "https://jobs.ashbyhq.com/supabase"),
    ("ElevenLabs",          "https://jobs.ashbyhq.com/elevenlabs"),
    ("Linear",              "https://jobs.ashbyhq.com/linear"),
    ("Replit",              "https://jobs.ashbyhq.com/replit"),
    ("Writer",              "https://jobs.ashbyhq.com/writer"),
    ("Baseten",             "https://jobs.ashbyhq.com/baseten"),
    ("Modal",               "https://jobs.ashbyhq.com/modal"),
    ("Browserbase",         "https://jobs.ashbyhq.com/browserbase"),
    ("Decagon",             "https://jobs.ashbyhq.com/decagon"),
    ("Fireworks AI",        "https://jobs.ashbyhq.com/fireworksai"),
    ("Dust",                "https://jobs.ashbyhq.com/dust"),
    ("LangChain",           "https://jobs.ashbyhq.com/langchain"),
    ("Cohere",              "https://jobs.ashbyhq.com/cohere"),
    ("Hightouch",           "https://jobs.ashbyhq.com/hightouch"),
    ("Monte Carlo",         "https://jobs.ashbyhq.com/montecarlodata"),
    ("Figure AI",           "https://jobs.ashbyhq.com/figure"),
    ("Anomalo",             "https://jobs.ashbyhq.com/anomalo"),
    ("Coalesce",            "https://jobs.ashbyhq.com/coalesce"),
    # Corrected from wrong GH slug → Ashby
    ("Benchling",           "https://jobs.ashbyhq.com/benchling"),
    ("Vanta",               "https://jobs.ashbyhq.com/vanta"),
    ("Thumbtack",           "https://jobs.ashbyhq.com/thumbtack"),
    ("Airbyte",             "https://jobs.ashbyhq.com/airbyte"),
    ("Confluent",           "https://jobs.ashbyhq.com/confluent"),
    ("Deel",                "https://jobs.ashbyhq.com/deel"),
    ("Drata",               "https://jobs.ashbyhq.com/drata"),
    ("Middesk",             "https://jobs.ashbyhq.com/middesk"),
    ("Snyk",                "https://jobs.ashbyhq.com/snyk"),
    ("Spring Health",       "https://jobs.ashbyhq.com/spring-health"),
    ("Strava",              "https://jobs.ashbyhq.com/strava"),
    ("Wiz",                 "https://jobs.ashbyhq.com/wiz"),
    ("Persona",             "https://jobs.ashbyhq.com/persona"),
    ("Lyra Health",         "https://jobs.ashbyhq.com/lyrahealth"),
    # Corrected from wrong Lever slug → Ashby
    ("Modern Treasury",     "https://jobs.ashbyhq.com/moderntreasury"),
    ("Temporal",            "https://jobs.ashbyhq.com/temporal"),
    ("Render",              "https://jobs.ashbyhq.com/render"),
    ("Runway",              "https://jobs.ashbyhq.com/runway"),
]

# ── DISCOVER ──────────────────────────────────────────────────────────────────
# Resolver probes slug variants across GH / Lever / Ashby and caches hits.
# Add freely — unknown companies are skipped silently.

DISCOVER = [
    # ── Data / ML infra & tooling ─────────────────────────────────────────────
    "Motherduck", "StarTree", "Imply", "Redpanda", "Estuary", "Materialize",
    "SingleStore", "PlanetScale", "Neon", "Turntable", "Lightdash",
    "Metabase", "Mode Analytics", "Grafana", "Sentry", "FullStory",
    "Heap", "Pendo", "New Relic", "Sumo Logic",
    "Weights & Biases", "Retool", "dbt Labs", "Census", "Tecton",
    "Sigma Computing", "Dataiku", "Snorkel AI", "Patronus AI",
    "Contextual AI", "Together AI", "Sana", "Hebbia", "Luma AI",

    # ── AI-native (newer / less certain ATS) ─────────────────────────────────
    "xAI", "Character.ai", "Midjourney", "Stability AI", "Mistral",
    "Hugging Face", "Pika Labs", "Magic", "Cognition AI", "Imbue",
    "Predibase", "Vellum", "Inflection AI", "Ideogram", "Suno",
    "1X Technologies", "Wayve", "Osmo", "Kling AI", "Adept", "Replicate",

    # ── Fintech ───────────────────────────────────────────────────────────────
    "Pipe", "Unit", "Column", "Lithic", "Expensify",
    "Blend", "Opendoor", "Parafin", "Lendio",
    "Rippling", "Eventbrite",

    # ── Enterprise / B2B SaaS ─────────────────────────────────────────────────
    "ClickUp", "Harness", "Buildkite", "Pulumi",
    "Drift", "Apollo.io", "Clay", "Common Room",
    "Demandbase", "Qualified",
    "Grammarly", "Coda", "HashiCorp", "Zendesk", "DocuSign",
    "Applied Intuition", "Tempus", "Hims & Hers",

    # ── Security ──────────────────────────────────────────────────────────────
    "Orca Security", "Secureframe", "Panther Labs", "Torq",
    "Strike Graph", "Tines", "Axonius", "Lacework",

    # ── Healthcare / Bio ──────────────────────────────────────────────────────
    "Ro", "Carbon Health", "Recursion Pharmaceuticals",
    "Insitro", "Veeva", "Flatiron Health", "Included Health",
    "Noom", "Calm", "Headspace",

    # ── Autonomous / Robotics ─────────────────────────────────────────────────
    "Aurora", "Motional", "Kodiak Robotics", "Gatik",
    "Ghost Autonomy", "Waabi", "Apptronik", "Agility Robotics",

    # ── Consumer / Social / Media ─────────────────────────────────────────────
    "ClassPass", "Peloton", "Bumble", "Hinge",
    "Spotify", "Netflix", "Twitch", "Match Group",

    # ── Cloud / Dev tools ─────────────────────────────────────────────────────
    "Fly.io", "Dagger", "Earthly", "Depot",
    "Buildkite", "CircleCI", "GitLab",

    # ── Other Bay Area notables ───────────────────────────────────────────────
    "Canva", "Wix", "Squarespace",
    "Splunk", "Dynatrace",

    # ── Life sciences / biotech ───────────────────────────────────────────────
    "Genentech", "23andMe", "Guardant Health", "10x Genomics", "Natera",
    "Pacific Biosciences", "Mammoth Biosciences", "Arcus Biosciences",
    "Vir Biotechnology", "CareDx", "Twist Bioscience", "Seer Bio",

    # ── Climate / clean energy ────────────────────────────────────────────────
    "Aurora Solar", "Sunrun", "Watershed", "Arcadia", "Stem",
    "Crusoe Energy", "Heirloom Carbon", "Twelve",

    # ── Gaming / entertainment ────────────────────────────────────────────────
    "Roblox", "Niantic", "Kabam", "Scopely",

    # ── Enterprise / B2B SaaS (new) ───────────────────────────────────────────
    "PagerDuty", "Workato", "Freshworks", "Gainsight",
    "Ironclad", "Procore", "Culture Amp", "Betterworks",
    "Miro", "Loom", "Calendly", "Zoom", "RingCentral",

    # ── Cybersecurity (new) ───────────────────────────────────────────────────
    "CrowdStrike", "SentinelOne", "Zscaler", "Exabeam", "Abnormal Security",

    # ── EdTech ────────────────────────────────────────────────────────────────
    "Chegg", "IXL Learning", "CodeSignal",

    # ── Consumer / marketplace ────────────────────────────────────────────────
    "Poshmark", "The RealReal", "AllTrails", "Life360", "Whatnot",

    # ── Logistics / supply chain ──────────────────────────────────────────────
    "Shippo", "EasyPost",

    # ── Data observability / experimentation ──────────────────────────────────
    "ThoughtSpot", "Atlan", "Datafold", "Statsig", "Eppo",
    "LaunchDarkly", "Prefect", "Dagster",

    # ── AI / ML tooling (new) ─────────────────────────────────────────────────
    "Arize AI", "Fiddler AI", "Deepgram", "AssemblyAI",
    "Labelbox", "Roboflow",

    # ── Crypto / Web3 ─────────────────────────────────────────────────────────
    "Ripple", "Alchemy",

    # ── HR tech ───────────────────────────────────────────────────────────────
    "15Five", "Leapsome",

    # ── PropTech ──────────────────────────────────────────────────────────────
    "Mynd",
]

# ── WORKDAY ───────────────────────────────────────────────────────────────────
# Requires confirmed host + tenant + site path. Add when validated.

WORKDAY = [
    ("Adobe",       "https://adobe.wd5.myworkdayjobs.com/external_experienced"),
    ("Nvidia",      "https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite"),
    ("Salesforce",  "https://salesforce.wd12.myworkdayjobs.com/External_Career_Site"),
    # Snowflake/ServiceNow/Twilio returned errors — need correct tenant paths
]

# ── FILTER LISTS ──────────────────────────────────────────────────────────────

INCLUDE_TITLE = [
    # Core DS / DE / AE
    "data scientist", "data engineer", "analytics engineer",
    "machine learning engineer", "ml engineer", "ai engineer",
    "applied scientist", "applied ml", "analytics scientist",
    "decision scientist", "research engineer",
    # BI
    "business intelligence", "bi engineer", "bi analyst",
    # Data analyst variants
    "data analyst",
    # People / HR analytics
    "people analyst", "people analytics", "workforce analyst", "workforce analytics",
    "hr analytics",
    # Product & growth
    "product analyst", "growth analyst",
    # Marketing
    "marketing analyst",
    # Finance-adjacent (data-heavy at tech cos)
    "revenue analyst",
    # Operations
    "operations analyst",
    # Customer / consumer insights
    "customer analytics", "customer insights", "consumer insights", "insights analyst",
    # Sales / GTM
    "sales analyst", "gtm analyst",
    # Pricing
    "pricing analyst", "pricing analytics",
    # Fraud / risk (data-heavy at fintech/payments)
    "fraud analyst", "fraud analytics",
    # Experimentation
    "experimentation analyst",
    # Quant
    "quantitative analyst", "quant analyst",
]

EXCLUDE_TITLE = [
    "intern", "internship",
]

SENIOR_TITLE = [
    "staff", "principal", "director", " vp", "vice president",
    "head of", "distinguished", "fellow", "senior", "sr.", " sr ",
    "lead", "manager", "management",
]

BAY_AREA = [
    # San Francisco Peninsula
    "san francisco", "south san francisco", "san mateo", "redwood city",
    "menlo park", "palo alto", "mountain view", "los altos", "los altos hills",
    "sunnyvale", "santa clara", "san jose", "cupertino", "milpitas",
    "foster city", "burlingame", "san bruno", "belmont", "san carlos",
    "half moon bay", "daly city", "brisbane",
    # East Bay
    "oakland", "emeryville", "berkeley", "alameda", "fremont", "newark",
    "union city", "hayward", "san leandro", "castro valley",
    "walnut creek", "pleasanton", "san ramon", "livermore", "dublin",
    "concord", "richmond", "el cerrito",
    # North Bay
    "marin", "san rafael", "novato", "sausalito", "mill valley",
    # General
    "bay area", "sf bay", "silicon valley",
]

SKILLS = [
    "sql", "python", "dbt", "snowflake", "spark", "airflow", "kafka",
    "bigquery", "redshift", "databricks", "looker", "tableau", "mode",
    "experimentation", "a/b test", "causal inference", "statistics",
    "machine learning", "llm", "llm eval", "rag", "fine-tuning",
    "data pipeline", "etl", "elt", "feature engineering", "mlflow",
    "scikit-learn", "pytorch", "tensorflow", "xgboost",
]

if __name__ == "__main__":
    total = len(VERIFIED) + len(DISCOVER) + len(WORKDAY)
    print(f"Registry: {len(VERIFIED)} verified + {len(DISCOVER)} to discover + {len(WORKDAY)} Workday = {total} total")
