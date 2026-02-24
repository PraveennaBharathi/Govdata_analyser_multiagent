from typing import Dict, Any, Optional
import logging
from config.settings import settings

# Optional imports - gracefully handle missing packages
try:
    from langchain_openai import ChatOpenAI
except ImportError:
    ChatOpenAI = None
    
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:
    ChatGoogleGenerativeAI = None
    
try:
    from langchain_mistralai import ChatMistralAI
except ImportError:
    ChatMistralAI = None

try:
    from langchain.schema import HumanMessage, SystemMessage
except ImportError:
    from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)

class LLMService:
    """LLM service with configurable primary/fallback based on settings"""
    
    def __init__(self):
        self.mistral_client = None
        self.gemini_client = None
        self.openai_client = None
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize LLM clients with correct models for each provider"""
        # Determine which model goes to which provider
        mistral_model = None
        gemini_model = None
        openai_model = None
        
        # Map models to providers based on model names
        for model in [settings.DEFAULT_MODEL, settings.FALLBACK_MODEL, settings.TERTIARY_MODEL]:
            if 'mistral' in model.lower():
                mistral_model = model
            elif 'gemini' in model.lower() or 'flash' in model.lower():
                gemini_model = model
            elif 'gpt' in model.lower():
                openai_model = model
        
        # Initialize Mistral
        try:
            if ChatMistralAI and settings.MISTRAL_API_KEY and mistral_model:
                self.mistral_client = ChatMistralAI(
                    model=mistral_model,
                    temperature=settings.TEMPERATURE,
                    mistral_api_key=settings.MISTRAL_API_KEY
                )
                logger.info(f"Mistral client initialized with model: {mistral_model}")
            elif not ChatMistralAI:
                logger.warning("langchain-mistralai not installed")
        except Exception as e:
            logger.error(f"Failed to initialize Mistral client: {e}")
        
        # Initialize Gemini
        try:
            if ChatGoogleGenerativeAI and settings.GEMINI_API_KEY and gemini_model:
                self.gemini_client = ChatGoogleGenerativeAI(
                    model=gemini_model,
                    temperature=settings.TEMPERATURE,
                    google_api_key=settings.GEMINI_API_KEY
                )
                logger.info(f"Gemini client initialized with model: {gemini_model}")
            elif not ChatGoogleGenerativeAI:
                logger.warning("langchain-google-genai not installed")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
        
        # Initialize OpenAI
        try:
            if ChatOpenAI and settings.OPENAI_API_KEY and openai_model:
                self.openai_client = ChatOpenAI(
                    model=openai_model,
                    temperature=settings.TEMPERATURE,
                    openai_api_key=settings.OPENAI_API_KEY
                )
                logger.info(f"OpenAI client initialized with model: {openai_model}")
            elif not ChatOpenAI:
                logger.warning("langchain-openai not installed")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
    
    async def generate_response(self, messages: list, fallback_level: int = 0) -> Optional[str]:
        """Generate response with multi-level fallback mechanism"""
        # Priority order: Mistral (primary), Gemini (fallback), OpenAI (tertiary)
        clients = [self.mistral_client, self.gemini_client, self.openai_client]
        client_names = ["Mistral", "Gemini", "OpenAI"]
        
        if fallback_level >= len(clients) or not clients[fallback_level]:
            logger.error("No LLM client available at fallback level")
            return None
        
        client = clients[fallback_level]
        client_name = client_names[fallback_level]
        
        try:
            response = await client.ainvoke(messages)
            logger.info(f"Response generated using {client_name}")
            return response.content
        except Exception as e:
            logger.error(f"{client_name} generation failed: {e}")
            if fallback_level + 1 < len(clients):
                next_client = client_names[fallback_level + 1]
                logger.info(f"Falling back to {next_client}")
                return await self.generate_response(messages, fallback_level + 1)
            return None
    
    async def parse_query(self, user_query: str) -> Dict[str, Any]:
        """Parse user query into structured format"""
        system_prompt = """You are a policy data analysis coordinator. Parse the user query into a structured JSON format.
        
        Return a JSON object with these exact keys:
        - dataset: the type of data (e.g., "employment", "population", "economy")
        - year_range: the year range as string (e.g., "2020-2024")
        - analysis: the type of analysis (e.g., "trend", "comparison", "correlation")
        
        Example:
        Input: "Show me employment trends from 2020 to 2024"
        Output: {"dataset": "employment", "year_range": "2020-2024", "analysis": "trend"}
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Parse this query: {user_query}")
        ]
        
        response = await self.generate_response(messages)
        
        if response:
            try:
                import json
                # Extract JSON from response
                start = response.find('{')
                end = response.rfind('}') + 1
                if start != -1 and end != 0:
                    json_str = response[start:end]
                    return json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM response as JSON: {e}")
        
        # Fallback to basic parsing
        return {
            "dataset": "employment",
            "year_range": "2020-2024", 
            "analysis": "trend"
        }
