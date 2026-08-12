"""
Shared configuration for the Auto FNOL Triage accelerator scripts.

Loads tenant-specific settings from environment variables (optionally via a local .env file,
using python-dotenv if installed) so no tenant-specific IDs, endpoints, or resource names are
hardcoded in the repo. Where a value is not required to be globally unique or is safe to default,
a sensible default name is generated automatically so you don't have to set every variable.

Quick start:
    1. Copy .env.example to .env in the repo root.
    2. Fill in the values that don't have safe defaults (workspace/lakehouse/project IDs,
       endpoints) — these are specific to your tenant and can't be guessed.
    3. Leave the rest as-is to use the generated default names, or override them.

All scripts in fabric/, foundry/, and datagen/ import from this module instead of hardcoding
values directly.
"""
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def _env(name, default=None, required=False):
    val = os.environ.get(name, default)
    if required and not val:
        raise RuntimeError(
            f"Required environment variable '{name}' is not set. "
            f"Copy .env.example to .env and fill it in, or export {name} in your shell."
        )
    return val


# ---------------------------------------------------------------------------
# Fabric — tenant-specific, no safe default (must be set to YOUR workspace/lakehouse)
# ---------------------------------------------------------------------------
FABRIC_WORKSPACE_ID = _env("FABRIC_WORKSPACE_ID", required=True)
FABRIC_LAKEHOUSE_ID = _env("FABRIC_LAKEHOUSE_ID", required=True)

# These are produced by fabric/create_ontology.py and fabric/configure_data_agent*.py on first
# run, and written to fabric/ontology_id.txt / fabric/data_agent_id.txt. Set them here (or via
# env) once you have them, so subsequent scripts (e.g. configure_data_agent_ontology.py) can
# find the existing ontology/graph model/data agent instead of re-creating them.
FABRIC_ONTOLOGY_ID = _env("FABRIC_ONTOLOGY_ID", default="")
FABRIC_GRAPH_MODEL_ID = _env("FABRIC_GRAPH_MODEL_ID", default="")
FABRIC_DATA_AGENT_ID = _env("FABRIC_DATA_AGENT_ID", default="")

# ---------------------------------------------------------------------------
# Fabric — safe defaults (override only if you want different display names)
# ---------------------------------------------------------------------------
FABRIC_LAKEHOUSE_NAME = _env("FABRIC_LAKEHOUSE_NAME", default="LH_AutoFNOL")
FABRIC_ONTOLOGY_NAME = _env("FABRIC_ONTOLOGY_NAME", default="AutoFNOL_Ontology")
FABRIC_DATA_AGENT_NAME = _env("FABRIC_DATA_AGENT_NAME", default="DA_AutoFNOL_Ontology")

# ---------------------------------------------------------------------------
# Azure AI Foundry — tenant-specific, no safe default
# ---------------------------------------------------------------------------
# Full project endpoint, e.g. https://<your-ai-foundry-resource>.services.ai.azure.com/api/projects/<your-project>
FOUNDRY_PROJECT_ENDPOINT = _env("FOUNDRY_PROJECT_ENDPOINT", required=True)

# ---------------------------------------------------------------------------
# Azure AI Foundry — safe defaults
# ---------------------------------------------------------------------------
FOUNDRY_MODEL_DEPLOYMENT = _env("FOUNDRY_MODEL_DEPLOYMENT", default="gpt-4o")
FOUNDRY_AGENT_NAME = _env("FOUNDRY_AGENT_NAME", default="Auto-FNOL-Knowledge-Agent")
FOUNDRY_SEARCH_CONNECTION_NAME = _env("FOUNDRY_SEARCH_CONNECTION_NAME", default="")  # auto-detected if blank

# ---------------------------------------------------------------------------
# Azure AI Search — tenant-specific endpoint, no safe default; index name has a default
# ---------------------------------------------------------------------------
# e.g. https://<your-search-service>.search.windows.net
AZURE_SEARCH_ENDPOINT = _env("AZURE_SEARCH_ENDPOINT", required=True)
AZURE_SEARCH_INDEX_NAME = _env("AZURE_SEARCH_INDEX_NAME", default="auto-fnol-kb-index")
AZURE_SEARCH_API_VERSION = _env("AZURE_SEARCH_API_VERSION", default="2024-07-01")

# Admin API key for Azure AI Search. Prefer leaving this unset and using Azure AD auth
# (az login) where the script supports it; only set AZURE_SEARCH_ADMIN_KEY if your search
# service has local (key-based) auth enabled and you want to use it instead.
AZURE_SEARCH_ADMIN_KEY = _env("AZURE_SEARCH_ADMIN_KEY", default="")

# ---------------------------------------------------------------------------
# Azure OpenAI embeddings (for foundry/build_search_index.py) — tenant-specific endpoint
# ---------------------------------------------------------------------------
# e.g. https://<your-aoai-resource>.cognitiveservices.azure.com
AZURE_OPENAI_ENDPOINT = _env("AZURE_OPENAI_ENDPOINT", required=True)
AZURE_OPENAI_API_VERSION = _env("AZURE_OPENAI_API_VERSION", default="2023-05-15")
AZURE_OPENAI_EMBEDDING_DEPLOYMENT = _env("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", default="text-embedding-ada-002")
AZURE_OPENAI_EMBEDDING_DIM = int(_env("AZURE_OPENAI_EMBEDDING_DIM", default="1536"))

# ---------------------------------------------------------------------------
# Output directory for generated sample data (datagen/) — defaults to datagen/output next to
# this repo, so no path needs to be set in most cases.
# ---------------------------------------------------------------------------
_REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
DATAGEN_OUTPUT_DIR = _env("DATAGEN_OUTPUT_DIR", default=os.path.join(_REPO_ROOT, "datagen", "output"))
