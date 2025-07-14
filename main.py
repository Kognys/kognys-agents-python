# main.py
import os
from dotenv import load_dotenv
from kognys.graph.builder import kognys_graph

# Load environment variables (like OPENAI_API_KEY)
load_dotenv()

def run_research(question: str):
    """Invokes the Kognys graph with a research question."""
    print(f"🚀 Starting research for: '{question}'")

    # The initial state for the graph
    initial_state = {"question": question}

    # Stream events from the graph execution
    for event in kognys_graph.stream(initial_state):
        # The event key is the name of the node that just ran
        node_name = list(event.keys())[0]
        node_output = event[node_name]
        print(f"\n✅ Node '{node_name}' finished.")
        print("---")
        print(node_output)

    print("\n🏁 Research complete.")


if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY is not set. Please create a .env file.")
    else:
        sample_question = "What are the latest advancements in battery technology for electric vehicles?"
        run_research(sample_question)
