"""
Create an Azure AI Foundry Agent for Auto FNOL Triage, wired to the Azure AI Search
knowledge base index (auto-fnol-kb-index) for RAG with citations.

This script also enables the Activity Protocol + BotServiceRbac authorization scheme on the
new agent's endpoint (see enable_activity_protocol() below) so it is immediately callable
from Copilot Studio / Teams / M365 Copilot — no separate script/step is required.

Project: set via FOUNDRY_PROJECT_ENDPOINT in .env
Model deployment: set via FOUNDRY_MODEL_DEPLOYMENT in .env
Search: set via FOUNDRY_SEARCH_CONNECTION_NAME / AZURE_SEARCH_INDEX_NAME in .env
"""
import os
import sys
from azure.identity import AzureCliCredential
from azure.ai.projects import AIProjectClient
from azure.ai.agents import AgentsClient
from azure.ai.agents.models import AzureAISearchTool, AzureAISearchQueryType
from azure.ai.projects.models import (
    ActivityProtocolConfiguration,
    AgentEndpointConfig,
    BotServiceRbacAuthorizationScheme,
    EntraAuthorizationScheme,
    ProtocolConfiguration,
    ResponsesProtocolConfiguration,
)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config

PROJECT_ENDPOINT = config.FOUNDRY_PROJECT_ENDPOINT
MODEL_DEPLOYMENT = config.FOUNDRY_MODEL_DEPLOYMENT
SEARCH_CONNECTION_NAME = config.FOUNDRY_SEARCH_CONNECTION_NAME
INDEX_NAME = config.AZURE_SEARCH_INDEX_NAME

AGENT_INSTRUCTIONS = """You are the Auto FNOL Knowledge Assistant for Contoso Insurance.
You answer questions from claims adjusters and the Copilot Studio orchestration agent about:
- Auto policy wording, coverage parts, and exclusions
- FNOL triage tiers and adjuster assignment rules
- SIU fraud referral red flags and process
- State regulatory claim-handling requirements (East States / South States)
- Subrogation identification methodology

Rules:
1. Always ground answers in the knowledge base via the search tool. Do not invent policy language.
2. Always cite the source document title/section when giving a rule or threshold.
3. If the knowledge base does not contain the answer, say so explicitly and recommend escalating to a claims supervisor.
4. Be concise and precise — adjusters need actionable, exact figures (e.g., SLA hours, deductible amounts, score thresholds).
5. When asked about fraud or subrogation scoring, present the criteria clearly as a checklist.
"""


def enable_activity_protocol(project: AIProjectClient, agent_name: str):
    """Enable the Activity Protocol + BotServiceRbac authorization scheme on the agent's
    stable endpoint. Required for the agent to be callable from Copilot Studio, Teams, or
    M365 Copilot — by default a newly created agent only serves the Responses protocol with
    Entra auth, which causes an "endpoint does not support activity" error otherwise. Not yet
    configurable via the Foundry portal UI (as of 2026); must be done via SDK/REST.
    Reference: https://learn.microsoft.com/azure/foundry/agents/how-to/configure-agent
    """
    endpoint_config = AgentEndpointConfig(
        protocol_configuration=ProtocolConfiguration(
            responses=ResponsesProtocolConfiguration(),
            activity=ActivityProtocolConfiguration(),
        ),
        authorization_schemes=[
            EntraAuthorizationScheme(),
            # An agent endpoint can only have ONE BotService-level scheme
            # (BotServiceRbac OR BotServiceTenant, not both).
            BotServiceRbacAuthorizationScheme(),
        ],
    )
    patched = project.agents.update_details(agent_name=agent_name, agent_endpoint=endpoint_config)
    print(f"Activity protocol enabled for agent: {patched.name}")
    print(patched.agent_endpoint)


def main():
    credential = AzureCliCredential()
    project = AIProjectClient(endpoint=PROJECT_ENDPOINT, credential=credential)

    # find the Azure AI Search connection registered on this project
    conn_id = None
    for conn in project.connections.list():
        print("connection found:", conn.name, conn.type)
        conn_type = str(getattr(conn, "type", "")).lower()
        is_search_conn = "azure" in conn_type and "search" in conn_type
        if SEARCH_CONNECTION_NAME:
            if conn.name == SEARCH_CONNECTION_NAME:
                conn_id = conn.id
        elif is_search_conn and not conn_id:
            conn_id = conn.id

    if not conn_id:
        if SEARCH_CONNECTION_NAME:
            print("No existing connection named", SEARCH_CONNECTION_NAME, "- attempting to create one is not supported via SDK; listing all connections above.")
        else:
            print("No Azure AI Search connection found to auto-select - attempting to create one is not supported via SDK; listing all connections above.")
        return

    search_tool = AzureAISearchTool(
        index_connection_id=conn_id,
        index_name=INDEX_NAME,
        query_type=AzureAISearchQueryType.SEMANTIC,
        top_k=5,
    )

    agents_client = AgentsClient(endpoint=PROJECT_ENDPOINT, credential=credential)

    # delete previous agent version if agent_id.txt exists, to avoid orphaned agents
    if os.path.exists("agent_id.txt"):
        with open("agent_id.txt") as f:
            old_id = f.read().strip()
        try:
            agents_client.delete_agent(old_id)
            print("Deleted old agent:", old_id)
        except Exception as e:
            print("Could not delete old agent (may not exist):", e)

    agent = agents_client.create_agent(
        model=MODEL_DEPLOYMENT,
        name=config.FOUNDRY_AGENT_NAME,
        instructions=AGENT_INSTRUCTIONS,
        tools=search_tool.definitions,
        tool_resources=search_tool.resources,
    )
    print("Created agent:", agent.id, agent.name)

    with open("agent_id.txt", "w") as f:
        f.write(agent.id)

    # Required so this agent can be called from Copilot Studio / Teams / M365 Copilot —
    # done here so it's not a separate manual step in the deployment process.
    enable_activity_protocol(project, agent.name)


if __name__ == "__main__":
    main()
