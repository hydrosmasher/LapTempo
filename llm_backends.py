\
from typing import Dict
import datetime, yaml

def render_prompts(question: str, context: str, prompts: Dict) -> Dict[str,str]:
    today = datetime.date.today().isoformat()
    system = prompts["system"].format(date=today, question=question, context=context)
    user = prompts["user"].format(date=today, question=question, context=context)
    return {"system": system, "user": user}

def call_llm(backend: str, model_name: str, messages: Dict[str,str]) -> str:
    if backend == "gpt4all":
        try:
            from gpt4all import GPT4All
            m = GPT4All(model_name)
            # Simple single-turn format
            prompt = messages["system"] + "\n\n" + messages["user"]
            out = m.generate(prompt, max_tokens=512, temp=0.2)
            return out.strip()
        except Exception as e:
            return f"[LLM error: {e}]\nContext answer (no generation possible)."
    elif backend == "ollama":
        try:
            import subprocess, json
            prompt = messages["system"] + "\n\n" + messages["user"]
            cmd = ["ollama", "run", model_name, prompt]
            out = subprocess.check_output(cmd, text=True)
            return out.strip()
        except Exception as e:
            return f"[LLM error: {e}]\nContext answer (no generation possible)."
    else:
        # No LLM: return the stitched context to let user read
        return "[No local LLM selected] Here are the most relevant snippets:\n\n" + messages["user"]
