"""
Prometheus metrics for TWISTED observability.
"""

import time
import logging
from prometheus_client import Counter, Histogram, Gauge

logger = logging.getLogger("twisted.monitoring")

# Case metrics
CASES_CREATED = Counter('twisted_cases_created_total', 'Total cases created', ['priority'])
CASES_COMPLETED = Counter('twisted_cases_completed_total', 'Total cases completed', ['outcome'])
CASE_DURATION = Histogram('twisted_case_duration_seconds', 'Time from creation to completion')

# Agent metrics
AGENT_THOUGHTS = Counter('twisted_agent_thoughts_total', 'Thoughts by agent', ['agent_id', 'state'])
DEBATE_ROUNDS = Histogram('twisted_debate_rounds', 'Rounds to convergence', ['consensus_reached'])

# Resource metrics
M4_THERMAL_STATE = Gauge('twisted_m4_thermal_state', 'Current thermal state (0=cool, 3=critical)')
GEMINI_RATE_LIMIT_HITS = Counter('twisted_gemini_rate_limit_hits_total', 'Rate limit events', ['model_tier'])
CHROMA_QUERY_DURATION = Histogram('twisted_chroma_query_duration_seconds', 'Vector search latency')

# Business metrics
DELIVERABLES_GENERATED = Counter('twisted_deliverables_generated_total', 'Reports, emails, etc.', ['type'])
USER_SATISFACTION = Gauge('twisted_user_satisfaction_score', 'Post-case rating')

class MetricsMiddleware:
    """FastAPI-style middleware for automatic metrics collection."""

    async def __call__(self, request, call_next):
        start_time = time.time()

        # Route-specific metrics logic could go here

        response = await call_next(request)

        duration = time.time() - start_time
        # Record generic request duration or specific metrics

        return response

def record_case_start(priority="normal"):
    CASES_CREATED.labels(priority=priority).inc()

def record_case_end(outcome="success", duration=0):
    CASES_COMPLETED.labels(outcome=outcome).inc()
    CASE_DURATION.observe(duration)

def record_agent_thought(agent_id, state="reasoning"):
    AGENT_THOUGHTS.labels(agent_id=agent_id, state=state).inc()
