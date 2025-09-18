\
import yaml
from router import handle_query

def load_yaml(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def main():
    cfg = load_yaml("config.yaml")
    prompts = load_yaml("prompts.yaml")
    print("HydroChat — Swimming Assistant (local)")
    print("Type your question (e.g., 'generate swim workout 4000m threshold free',")
    print("'dryland core 30', 'analyze pace laps=[85,86,86,87] rest=[20,20,25] hr=[160,165,168]',")
    print("'injury shoulder', 'nutrition vegan', or anything else for RAG). Type 'exit' to quit.\n")

    while True:
        q = input("You: ").strip()
        if not q:
            continue
        if q.lower() in {"exit", "quit"}:
            break
        ans = handle_query(q, cfg, prompts)
        print("\nAssistant:\n", ans, "\n")

if __name__ == "__main__":
    main()
