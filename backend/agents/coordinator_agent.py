from typing import Dict, Any, List
import logging
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field
from services.llm_service import LLMService
from agents.extraction.extraction_agent import ExtractionAgent
from agents.analytics.analytics_agent import AnalyticsAgent

logger = logging.getLogger(__name__)

class AgentState(BaseModel):
    """State for agent coordination"""
    user_query: str
    parsed_query: Dict[str, Any] = {}
    analysis_plan: List[str] = []
    current_step: str = ""
    extracted_data: List[Dict] = []
    data_info: Dict[str, Any] = {}
    analysis_result: Dict[str, Any] = {}
    result: Dict[str, Any] = {}
    status: str = "pending"

class CoordinatorAgent:
    """Coordinator Agent for planning and managing analysis workflows"""
    
    def __init__(self):
        self.llm_service = LLMService()
        self.extraction_agent = ExtractionAgent()
        self.analytics_agent = AnalyticsAgent()
        self.graph = self._build_graph()
    
    def _build_graph(self):
        """Build the LangGraph workflow"""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("parse_query", self._parse_query)
        workflow.add_node("create_plan", self._create_analysis_plan)
        workflow.add_node("extract_data", self._extract_data)
        workflow.add_node("analyze_data", self._analyze_data)
        workflow.add_node("generate_final_result", self._generate_final_result)
        
        # Add edges
        workflow.add_edge(START, "parse_query")
        workflow.add_edge("parse_query", "create_plan")
        workflow.add_edge("create_plan", "extract_data")
        workflow.add_edge("extract_data", "analyze_data")
        workflow.add_edge("analyze_data", "generate_final_result")
        workflow.add_edge("generate_final_result", END)
        
        return workflow.compile()
    
    async def _parse_query(self, state: AgentState) -> AgentState:
        """Parse user query into structured format"""
        logger.info(f"Parsing query: {state.user_query}")
        
        try:
            parsed = await self.llm_service.parse_query(state.user_query)
            state.parsed_query = parsed
            state.current_step = "query_parsed"
            logger.info(f"Query parsed: {parsed}")
        except Exception as e:
            logger.error(f"Query parsing failed: {e}")
            state.parsed_query = {
                "dataset": "employment",
                "year_range": "2020-2024",
                "analysis": "trend"
            }
        
        return state
    
    async def _create_analysis_plan(self, state: AgentState) -> AgentState:
        """Create analysis plan based on parsed query"""
        logger.info("Creating analysis plan")
        
        dataset = state.parsed_query.get("dataset", "employment")
        analysis_type = state.parsed_query.get("analysis", "trend")
        year_range = state.parsed_query.get("year_range", "2020-2024")
        
        # Simple planning logic
        plan = [
            f"Extract {dataset} data for {year_range}",
            f"Perform {analysis_type} analysis",
            "Generate insights and visualizations",
            "Create structured report"
        ]
        
        state.analysis_plan = plan
        state.current_step = "plan_created"
        logger.info(f"Analysis plan created: {plan}")
        
        return state
    
    async def _extract_data(self, state: AgentState) -> AgentState:
        """Extract data using Extraction Agent"""
        logger.info("Extracting data")
        
        # Check if requested dataset is supported
        requested_dataset = state.parsed_query.get("dataset", "employment")
        supported_datasets = ["employment", "labor", "workforce", "jobs"]
        
        if requested_dataset not in supported_datasets and requested_dataset != "employment":
            # User asked for unsupported data (GDP, economy, etc.)
            logger.warning(f"Unsupported dataset requested: {requested_dataset}")
            state.extracted_data = []
            state.data_info = {
                "unsupported_dataset": requested_dataset,
                "available_datasets": ["employment", "labor force", "workforce statistics"]
            }
            state.current_step = "unsupported_dataset"
            return state
        
        try:
            # Extract employment data
            extraction_result = self.extraction_agent.load_employment_data()
            
            if extraction_result["status"] == "success":
                state.extracted_data = extraction_result["data"]
                state.data_info = extraction_result.get("data_info", {})
                state.current_step = "data_extracted"
                logger.info(f"Data extracted: {len(state.extracted_data)} records")
            else:
                logger.error(f"Data extraction failed: {extraction_result.get('error')}")
                state.extracted_data = []
                state.data_info = {}
                state.current_step = "extraction_failed"
                
        except Exception as e:
            logger.error(f"Data extraction error: {e}")
            state.extracted_data = []
            state.data_info = {}
            state.current_step = "extraction_failed"
        
        return state
    
    async def _analyze_data(self, state: AgentState) -> AgentState:
        """Analyze data using Analytics Agent"""
        logger.info("Analyzing data")
        
        # Check if we have an unsupported dataset request
        if state.current_step == "unsupported_dataset":
            requested = state.data_info.get("unsupported_dataset", "unknown")
            available = state.data_info.get("available_datasets", [])
            
            state.analysis_result = {
                "status": "unsupported",
                "conversational_response": f"I apologize, but I currently only have access to employment and workforce data from Singapore government sources (data.gov.sg, MOM, and SingStat). I cannot analyze {requested} data such as GDP, economic indicators, or other macroeconomic metrics at this time.\n\nHowever, I can help you analyze:\n- Employment trends across sectors (Construction, Manufacturing, Services)\n- Workforce statistics and labor force data\n- Year-over-year employment growth patterns\n- Sector-specific employment analysis\n\nWould you like me to analyze employment trends instead? You can ask questions like:\n- 'Analyze employment trends from 2020 to 2024'\n- 'Compare unemployment rates across different sectors'\n- 'Show me workforce growth patterns'",
                "summary_statistics": {},
                "insights": [f"System currently supports employment data only, not {requested} data"],
                "yearly_trends": [],
                "sector_trends": []
            }
            state.current_step = "analysis_completed"
            return state
        
        if not state.extracted_data:
            logger.warning("No data to analyze")
            state.analysis_result = {"status": "error", "error": "No data available"}
            state.current_step = "analysis_failed"
            return state
        
        try:
            # Perform trend analysis
            analysis_result = await self.analytics_agent.analyze_employment_trends(state.extracted_data)
            state.analysis_result = analysis_result
            state.current_step = "analysis_completed"
            logger.info("Data analysis completed")
            
        except Exception as e:
            logger.error(f"Data analysis error: {e}")
            state.analysis_result = {"status": "error", "error": str(e)}
            state.current_step = "analysis_failed"
        
        return state
    
    async def _generate_final_result(self, state: AgentState) -> AgentState:
        """Generate final result combining all outputs"""
        logger.info("Generating final result")
        
        # Extract conversational response for prominent display
        conversational_response = state.analysis_result.get("conversational_response", "")
        
        # Generate structured report with citations
        extraction_info = {
            "sources_loaded": state.data_info.get("sources_loaded", []) if state.data_info else [],
            "records_count": len(state.extracted_data),
            "quality_score": state.data_info.get("validation_report", {}).get("quality_score", 0) if state.data_info else 0
        }
        
        # Use report generator from analytics agent
        structured_report = None
        if hasattr(self.analytics_agent, 'report_generator'):
            try:
                structured_report = self.analytics_agent.report_generator.generate_structured_report(
                    query=state.user_query,
                    analysis_result=state.analysis_result,
                    extraction_info=extraction_info,
                    parsed_query=state.parsed_query
                )
            except Exception as e:
                logger.error(f"Report generation failed: {e}")
        
        state.result = {
            "query": state.user_query,
            "conversational_response": conversational_response,
            "parsed_query": state.parsed_query,
            "analysis_plan": state.analysis_plan,
            "extraction_summary": {
                "status": "success" if state.extracted_data else "failed",
                "records_count": len(state.extracted_data),
                "sources": extraction_info.get("sources_loaded", [])
            },
            "analysis": state.analysis_result,
            "structured_report": structured_report,
            "status": "completed" if state.analysis_result.get("status") == "success" else "failed"
        }
        
        state.status = state.result["status"]
        state.current_step = "completed"
        
        return state
    
    async def process_query(self, user_query: str) -> Dict[str, Any]:
        """Process user query through the agent workflow"""
        logger.info(f"Processing query: {user_query}")
        
        initial_state = AgentState(user_query=user_query)
        
        try:
            # Execute the workflow
            final_state = await self.graph.ainvoke(initial_state)
            
            # Handle both dict and AgentState returns
            if isinstance(final_state, dict):
                parsed_query = final_state.get("parsed_query", {})
                analysis_plan = final_state.get("analysis_plan", [])
                result = final_state.get("result", {})
            else:
                parsed_query = final_state.parsed_query
                analysis_plan = final_state.analysis_plan
                result = final_state.result
            
            return {
                "status": "success",
                "parsed_query": parsed_query,
                "analysis_plan": analysis_plan,
                "result": result,
                "workflow_steps": [
                    "parse_query",
                    "create_plan",
                    "extract_data",
                    "analyze_data",
                    "generate_final_result"
                ]
            }
        except Exception as e:
            logger.error(f"Query processing failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "status": "error",
                "error": str(e),
                "parsed_query": {},
                "analysis_plan": [],
                "result": {}
            }
