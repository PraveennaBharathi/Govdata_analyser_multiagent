from typing import Dict, Any, Optional, List
import logging
from config.settings import settings

logger = logging.getLogger(__name__)

try:
    from langchain_mistralai import ChatMistralAI
except ImportError:
    ChatMistralAI = None

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:
    ChatGoogleGenerativeAI = None

try:
    from langchain_ollama import ChatOllama
except ImportError:
    ChatOllama = None

try:
    from langchain_core.messages import HumanMessage, SystemMessage
except ImportError:
    from langchain_core.messages import HumanMessage, SystemMessage


class LLMService:
    """
    Three-tier LLM service:
      Tier 1 — Ollama (local, qwen2.5:14b)    — unlimited, ~25 tok/s, no cost
      Tier 2 — Mistral API (tiered by task)   — routing/narrative/reasoning models
      Tier 3 — Gemini (cloud fallback)         — last resort
    """

    def __init__(self):
        self._routing_client  = None   # fast JSON routing
        self._narrative_client = None  # quality narrative writing
        self._reasoning_client = None  # chain-of-thought cross-domain
        self._local_client    = None   # Ollama — unlimited calls
        self._gemini_client   = None   # fallback
        self._init()

    def _init(self):
        # ── Ollama (Tier 1, local) ──────────────────────────────────────
        if ChatOllama:
            try:
                self._local_client = ChatOllama(
                    model=settings.OLLAMA_MODEL,
                    base_url=settings.OLLAMA_BASE_URL,
                    temperature=settings.TEMPERATURE,
                )
                logger.info(f"Ollama client ready: {settings.OLLAMA_MODEL}")
            except Exception as e:
                logger.warning(f"Ollama init failed (server down?): {e}")

        # ── Mistral API (Tier 2, three sub-models) ─────────────────────
        if ChatMistralAI and settings.MISTRAL_API_KEY:
            for attr, model, label in [
                ("_routing_client",   settings.MISTRAL_ROUTING_MODEL,   "routing"),
                ("_narrative_client", settings.MISTRAL_NARRATIVE_MODEL,  "narrative"),
                ("_reasoning_client", settings.MISTRAL_REASONING_MODEL,  "reasoning"),
            ]:
                try:
                    setattr(self, attr, ChatMistralAI(
                        model=model,
                        temperature=settings.TEMPERATURE,
                        mistral_api_key=settings.MISTRAL_API_KEY,
                    ))
                    logger.info(f"Mistral {label} ready: {model}")
                except Exception as e:
                    logger.error(f"Mistral {label} init failed: {e}")

        # ── Gemini (Tier 3, fallback) ───────────────────────────────────
        if ChatGoogleGenerativeAI and settings.GEMINI_API_KEY:
            try:
                self._gemini_client = ChatGoogleGenerativeAI(
                    model=settings.GEMINI_MODEL,
                    temperature=settings.TEMPERATURE,
                    google_api_key=settings.GEMINI_API_KEY,
                )
                logger.info(f"Gemini fallback ready: {settings.GEMINI_MODEL}")
            except Exception as e:
                logger.error(f"Gemini init failed: {e}")

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    async def generate_response(self, messages: list, mode: str = "narrative") -> Optional[str]:
        """
        Generate a response using the appropriate model tier.

        mode options:
          "routing"   — fast JSON classification (mistral-small, 50 req/min)
          "narrative" — quality prose output (mistral-large, 4 req/min)
          "reasoning" — chain-of-thought analysis (magistral, 5 req/min)
          "local"     — always use Ollama, no API calls (unlimited)
        """
        chain = self._build_chain(mode)
        for client, name in chain:
            try:
                response = await client.ainvoke(messages)
                content = response.content
                # magistral returns thinking blocks as a list
                if isinstance(content, list):
                    text_parts = [
                        block.get("text", "") if isinstance(block, dict) else str(block)
                        for block in content
                        if not (isinstance(block, dict) and block.get("type") == "thinking")
                    ]
                    content = " ".join(text_parts).strip()
                logger.info(f"Response via {name} ({mode} mode)")
                return content
            except Exception as e:
                logger.warning(f"{name} failed ({mode}): {e}")
        logger.error(f"All clients failed for mode={mode}")
        return None

    async def parse_query(self, user_query: str) -> Dict[str, Any]:
        """
        Parse user query into structured routing object.
        Uses routing model (fast + JSON-accurate).
        """
        system_prompt = """You are a Singapore government data analytics coordinator.
Parse the user query and return a JSON object with these exact keys:

- domain: one of "labour" | "housing" | "business" | "transport" | "environment" | "demographics" | "cross_domain"
  * labour: employment, jobs, unemployment, retrenchment, workforce, MOM, wages, recruitment, layoffs
  * housing: HDB, resale, flat, BTO, property, housing prices, rental, town, estate, condo
  * business: ACRA, companies, startups, registrations, COE, retail, trade, economy
  * transport: MRT, LRT, bus, ridership, commute, train, stations
  * environment: PSI, air quality, dengue, weather, haze, PM2.5
  * demographics: population, age, residents, planning area, elderly, families
  * cross_domain: query spans multiple domains (e.g. housing + labour, transport + property)

- dataset: specific dataset
  * labour: "labour_market" (default) | "unemployment_rate" | "retrenchment" | "recruitment_rate"
  * housing: "hdb_resale" | "private_property"
  * business: "acra" | "coe" | "retail"
  * transport: "mrt_ridership"
  * environment: "psi" | "dengue"
  * demographics: "population"
  * cross_domain: "multi" (always)

- year_range: "2020-2025" (extract from query or default)
- analysis: "trend" | "comparison" | "ranking" | "composite" | "correlation"
- filters: {"town": "TAMPINES", "flat_type": "4 ROOM"} — only for housing queries

Return ONLY valid JSON, no other text."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Parse: {user_query}")
        ]

        response = await self.generate_response(messages, mode="routing")

        if response:
            try:
                import json
                start = response.find('{')
                end = response.rfind('}') + 1
                if start != -1 and end > 0:
                    parsed = json.loads(response[start:end])
                    if "domain" in parsed:
                        return parsed
            except Exception as e:
                logger.error(f"JSON parse failed: {e}")

        # Keyword fallback
        return self._keyword_fallback(user_query)

    # ------------------------------------------------------------------ #
    #  Private helpers                                                     #
    # ------------------------------------------------------------------ #

    def _build_chain(self, mode: str) -> List[tuple]:
        """
        Build ordered fallback chain for a given mode.
        Local (Ollama) is always available as a fallback so the app
        never goes completely dark even if all APIs are down.
        """
        if mode == "routing":
            # Speed matters most — Mistral small is sub-second
            candidates = [
                (self._routing_client,  "Mistral-Small (routing)"),
                (self._local_client,    "Ollama-local (routing fallback)"),
                (self._gemini_client,   "Gemini (routing fallback)"),
            ]
        elif mode == "reasoning":
            # Chain-of-thought — magistral first, then large, then local
            candidates = [
                (self._reasoning_client, "Magistral (reasoning)"),
                (self._narrative_client, "Mistral-Large (reasoning fallback)"),
                (self._local_client,     "Ollama-local (reasoning fallback)"),
                (self._gemini_client,    "Gemini (reasoning fallback)"),
            ]
        elif mode == "local":
            # Force local — used for background tasks, auto-summaries
            candidates = [
                (self._local_client,    "Ollama-local"),
                (self._narrative_client,"Mistral-Large (local fallback)"),
                (self._gemini_client,   "Gemini (local fallback)"),
            ]
        else:  # "narrative" (default)
            # Quality matters — large model first, then local
            candidates = [
                (self._narrative_client, "Mistral-Large (narrative)"),
                (self._local_client,     "Ollama-local (narrative fallback)"),
                (self._gemini_client,    "Gemini (narrative fallback)"),
            ]

        return [(c, name) for c, name in candidates if c is not None]

    def _keyword_fallback(self, query: str) -> Dict[str, Any]:
        q = query.lower()
        if any(w in q for w in ["hdb", "resale", "flat", "housing", "bto", "town", "estate"]):
            return {"domain": "housing", "dataset": "hdb_resale",
                    "year_range": "2020-2025", "analysis": "price_trend", "filters": {}}
        if any(w in q for w in ["condo", "private", "ura", "landed"]):
            return {"domain": "housing", "dataset": "private_property",
                    "year_range": "2020-2025", "analysis": "price_trend", "filters": {}}
        if any(w in q for w in ["mrt", "lrt", "ridership", "train", "bus", "commute"]):
            return {"domain": "transport", "dataset": "mrt_ridership",
                    "year_range": "2020-2025", "analysis": "trend", "filters": {}}
        if any(w in q for w in ["psi", "air", "haze", "pm2.5", "pollution"]):
            return {"domain": "environment", "dataset": "psi",
                    "year_range": "2020-2025", "analysis": "trend", "filters": {}}
        if any(w in q for w in ["dengue", "cluster", "mosquito"]):
            return {"domain": "environment", "dataset": "dengue",
                    "year_range": "2020-2025", "analysis": "trend", "filters": {}}
        if any(w in q for w in ["acra", "company", "startup", "business", "register"]):
            return {"domain": "business", "dataset": "acra",
                    "year_range": "2020-2025", "analysis": "trend", "filters": {}}
        if any(w in q for w in ["coe", "car", "vehicle"]):
            return {"domain": "business", "dataset": "coe",
                    "year_range": "2020-2025", "analysis": "trend", "filters": {}}
        if any(w in q for w in ["population", "resident", "demographic", "elderly", "age"]):
            return {"domain": "demographics", "dataset": "population",
                    "year_range": "2020-2025", "analysis": "trend", "filters": {}}
        if any(w in q for w in ["unemployment", "retrench", "recruit", "workforce", "labour", "labor", "job", "employ"]):
            return {"domain": "labour", "dataset": "labour_market",
                    "year_range": "2020-2025", "analysis": "composite", "filters": {}}
        # Default — labour market composite
        return {"domain": "labour", "dataset": "labour_market",
                "year_range": "2020-2025", "analysis": "composite", "filters": {}}
