"""Quick test: send a question to the Auto FNOL Knowledge Agent and print the grounded answer + citations."""
import os
import sys
from azure.identity import AzureCliCredential
from azure.ai.agents import AgentsClient
from azure.ai.agents.models import ListSortOrder

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config

PROJECT_ENDPOINT = config.FOUNDRY_PROJECT_ENDPOINT

with open("agent_id.txt") as f:
    AGENT_ID = f.read().strip()

QUESTIONS = [
    "What is the total loss threshold in East States vs South States?",
    "What fraud score threshold requires mandatory SIU referral?",
    "What SLA applies for first adjuster contact on a Tier 3 complex claim?",
]


def main():
    credential = AzureCliCredential()
    client = AgentsClient(endpoint=PROJECT_ENDPOINT, credential=credential)

    thread = client.threads.create()
    print("Thread:", thread.id)

    for q in QUESTIONS:
        client.messages.create(thread_id=thread.id, role="user", content=q)
        run = client.runs.create_and_process(thread_id=thread.id, agent_id=AGENT_ID)
        print(f"\nQ: {q}")
        print("Run status:", run.status)
        if run.status == "failed":
            print("Error:", run.last_error)
            continue
        messages = client.messages.list(thread_id=thread.id, order=ListSortOrder.DESCENDING, limit=1)
        for m in messages:
            for c in m.content:
                if hasattr(c, "text"):
                    print("A:", c.text.value[:600].encode("ascii", "ignore").decode())


if __name__ == "__main__":
    main()
