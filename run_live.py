# run_live.py
import uuid
from kognys.graph.builder import kognys_graph
from kognys.graph.state import KognysState

def main():
    # ... (setup code is the same) ...
    research_question = "What are the most promising applications of generative AI in software development?"
    print("...")

    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    initial_state = KognysState(question=research_question)

    # Use .stream() to see the output from each node as it runs
    for i, chunk in enumerate(kognys_graph.stream(initial_state, config=config)):
        # --- Start of Changes ---
        # Add a guard clause to skip empty or invalid chunks
        if not chunk:
            continue
        
        node_name, state_update = list(chunk.items())[0]
        
        # Another guard clause for safety
        if state_update is None:
            continue
        # --- End of Changes ---

        print(f"\n--- ➡️ STEP {i+1}: EXECUTING NODE '{node_name}' ---")
        
        # The rest of the logging logic remains the same
        if 'validated_question' in state_update:
            print(f"  - Validated Question: \"{state_update['validated_question']}\"")
        if 'documents' in state_update:
            print(f"  - Retrieved {len(state_update['documents'])} documents.")
        # ... (and so on for the other keys) ...
        if 'final_answer' in state_update:
            print("\n" + "="*60)
            print("✅ FINAL ANSWER")
            print("="*60)
            print(state_update['final_answer'])

if __name__ == "__main__":
    main()
