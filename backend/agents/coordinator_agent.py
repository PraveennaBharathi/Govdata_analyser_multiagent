from typing import Dict, Any, List
import logging
import time
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
    node_timings: Dict[str, float] = {}

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
        t0 = time.time()
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

        state.node_timings["parse_query"] = round((time.time() - t0) * 1000)
        return state
    
    async def _create_analysis_plan(self, state: AgentState) -> AgentState:
        """Create analysis plan based on parsed query"""
        t0 = time.time()
        logger.info("Creating analysis plan")

        dataset = state.parsed_query.get("dataset", "employment")
        analysis_type = state.parsed_query.get("analysis", "trend")
        year_range = state.parsed_query.get("year_range", "2020-2024")

        plan = [
            f"Extract {dataset} data for {year_range}",
            f"Perform {analysis_type} analysis",
            "Generate insights and visualizations",
            "Create structured report"
        ]

        state.analysis_plan = plan
        state.current_step = "plan_created"
        logger.info(f"Analysis plan created: {plan}")

        state.node_timings["create_plan"] = round((time.time() - t0) * 1000)
        return state
    
    async def _extract_data(self, state: AgentState) -> AgentState:
        """Extract data — routes by domain (labour / housing)."""
        t0 = time.time()
        domain = state.parsed_query.get("domain", "labour")
        dataset = state.parsed_query.get("dataset", "employment_trends")
        filters = state.parsed_query.get("filters", {})
        logger.info(f"Extracting data: domain={domain} dataset={dataset}")

        try:
            if domain == "housing":
                result = self.extraction_agent.load_hdb_data(filters=filters)
            elif domain == "cross_domain":
                # Cross-domain analytics handles its own extraction internally
                state.extracted_data = []
                state.data_info = {"note": "cross_domain_self_loads"}
                state.current_step = "data_extracted"
                state.node_timings["extract_data"] = round((time.time() - t0) * 1000)
                return state
            else:
                # All labour / unknown queries use the composite live dataset
                result = self.extraction_agent.load_labour_market_data()

            if result["status"] == "success":
                state.extracted_data = result["data"]
                state.data_info = result.get("data_info", {})
                state.current_step = "data_extracted"
                logger.info(f"Extracted {len(state.extracted_data)} records [{domain}/{dataset}]")
            else:
                logger.error(f"Extraction failed: {result.get('error')}")
                state.extracted_data = []
                state.data_info = {}
                state.current_step = "extraction_failed"

        except Exception as e:
            logger.error(f"Data extraction error: {e}")
            import traceback; logger.error(traceback.format_exc())
            state.extracted_data = []
            state.data_info = {}
            state.current_step = "extraction_failed"

        state.node_timings["extract_data"] = round((time.time() - t0) * 1000)
        return state
    
    async def _analyze_data(self, state: AgentState) -> AgentState:
        """Analyze data using Analytics Agent"""
        t0 = time.time()
        logger.info("Analyzing data")

        domain = state.parsed_query.get("domain", "labour")

        if not state.extracted_data and domain != "cross_domain":
            logger.warning("No data to analyze")
            state.analysis_result = {"status": "error", "error": "No data available for the requested query."}
            state.current_step = "analysis_failed"
            state.node_timings["analyze_data"] = round((time.time() - t0) * 1000)
            return state

        try:
            if domain == "housing":
                analysis_result = await self.analytics_agent.analyze_hdb_data(
                    state.extracted_data, state.parsed_query
                )
            elif domain == "cross_domain":
                parsed_with_query = {**state.parsed_query, "user_query": state.user_query}
                analysis_result = await self.analytics_agent.analyze_cross_domain(parsed_with_query)
            else:
                analysis_result = await self.analytics_agent.analyze_labour_market(
                    state.extracted_data, state.parsed_query
                )

            state.analysis_result = analysis_result
            state.current_step = "analysis_completed"
            logger.info(f"Analysis completed [{domain}]")

        except Exception as e:
            logger.error(f"Data analysis error: {e}")
            import traceback; logger.error(traceback.format_exc())
            state.analysis_result = {"status": "error", "error": str(e)}
            state.current_step = "analysis_failed"

        state.node_timings["analyze_data"] = round((time.time() - t0) * 1000)
        return state
    
    async def _generate_final_result(self, state: AgentState) -> AgentState:
        """Generate final result combining all outputs"""
        t0 = time.time()
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
        
        state.node_timings["generate_final_result"] = round((time.time() - t0) * 1000)
        state.status = state.result["status"]
        state.current_step = "completed"

        return state
    
    async def process_query(self, user_query: str) -> Dict[str, Any]:
        """Process user query through the agent workflow"""
        logger.info(f"Processing query: {user_query}")

        initial_state = AgentState(user_query=user_query)

        NODE_META = {
            "parse_query":            {"label": "Parse Query",           "icon": "brain"},
            "create_plan":            {"label": "Create Analysis Plan",  "icon": "list"},
            "extract_data":           {"label": "Extract Data",          "icon": "database"},
            "analyze_data":           {"label": "Analyze Data",          "icon": "chart"},
            "generate_final_result":  {"label": "Generate Report",       "icon": "file"},
        }

        try:
            final_state = await self.graph.ainvoke(initial_state)

            if isinstance(final_state, dict):
                parsed_query = final_state.get("parsed_query", {})
                analysis_plan = final_state.get("analysis_plan", [])
                result = final_state.get("result", {})
                node_timings = final_state.get("node_timings", {})
            else:
                parsed_query = final_state.parsed_query
                analysis_plan = final_state.analysis_plan
                result = final_state.result
                node_timings = final_state.node_timings

            workflow_steps = [
                {
                    "step": node,
                    "label": NODE_META[node]["label"],
                    "icon": NODE_META[node]["icon"],
                    "status": "completed",
                    "duration_ms": node_timings.get(node, 0),
                }
                for node in NODE_META
            ]

            return {
                "status": "success",
                "parsed_query": parsed_query,
                "analysis_plan": analysis_plan,
                "result": result,
                "workflow_steps": workflow_steps,
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
                "result": {},
                "workflow_steps": [],
            }
