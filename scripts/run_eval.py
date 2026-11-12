"""Run the MCQ test on one model and save the answers.

Usage (from the repo root):
  python scripts/run_eval.py --provider gemini --model gemini-2.5-flash --mode nastaliq
  python scripts/run_eval.py --provider gemini --model gemini-2.5-flash --mode roman
  python scripts/run_eval.py --provider groq --model llama-3.3-70b-versatile --mode nastaliq

Providers and the key each one reads from the environment:
  gemini      GEMINI_API_KEY
  groq        GROQ_API_KEY
  openrouter  OPENROUTER_API_KEY
  openai      OPENAI_API_KEY

--mode nastaliq shows the proverb in Nastaliq script; --mode roman shows the
transliteration. The script is safe to re-run: ids already answered are skipped.
"""
import argparse
import csv
import json
import os
import re
import time
import urllib.error
import urllib.request

OPENAI_STYLE = {
    "groq": "https://api.groq.com/openai/v1/chat/completions",
    "openrouter": "https://openrouter.ai/api/v1/chat/completions",
    "openai": "https://api.openai.com/v1/chat/completions",
}
KEYS = {"gemini": "GEMINI_API_KEY", "groq": "GROQ_API_KEY",
        "openrouter": "OPENROUTER_API_KEY", "openai": "OPENAI_API_KEY"}

PROMPT = """The following is a Kashmiri proverb.

Proverb: {proverb}

Which option best gives the meaning of this proverb?
A. {a}
B. {b}
C. {c}
D. {d}

Answer with only one letter: A, B, C or D."""


FOLLOWUP = ("Based on your analysis above, what is your final answer? "
            "Reply with only one letter: A, B, C or D.")


def post(url, payload, headers):
    req = urllib.request.Request(url, json.dumps(payload).encode("utf-8"),
                                 {"Content-Type": "application/json",
                                  "User-Agent": "kashmiri-proverb-eval/1.0", **headers})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode("utf-8"))


def ask(provider, model, key, prompt, max_tokens=2048, effort=None, turns=None):
    """turns = optional earlier conversation: [("user", text), ("assistant", text), ...]"""
    msgs = list(turns) if turns else [("user", prompt)]
    if provider == "gemini":
        url = ("https://generativelanguage.googleapis.com/v1beta/models/"
               f"{model}:generateContent?key={key}")
        contents = [{"role": "user" if r == "user" else "model", "parts": [{"text": t}]}
                    for r, t in msgs]
        out = post(url, {"contents": contents,
                         "generationConfig": {"temperature": 0, "maxOutputTokens": max_tokens}}, {})
        return out["candidates"][0]["content"]["parts"][0]["text"]
    body = {"model": model, "temperature": 0, "max_tokens": max_tokens,
            "messages": [{"role": r, "content": t} for r, t in msgs]}
    if effort == "off" and provider == "openrouter":
        body["reasoning"] = {"enabled": False}
    elif effort and provider == "openrouter":
        body["reasoning"] = {"effort": effort}
    elif effort:
        body["reasoning_effort"] = effort
    out = post(OPENAI_STYLE[provider], body, {"Authorization": f"Bearer {key}"})
    choice = out["choices"][0]
    text = choice["message"].get("content") or ""
    if not text.strip():
        print("  empty answer, finish_reason =", choice.get("finish_reason"))
    return text


def ask_retry(*args, tries=7, **kw):
    """Retry on rate-limit / overload errors, waiting longer each time."""
    for i in range(tries):
        try:
            return ask(*args, **kw)
        except urllib.error.HTTPError as e:
            try:
                body = e.read().decode("utf-8", "replace")[:300].replace("\n", " ")
            except Exception:
                body = ""
            print(f"  HTTP {e.code} reason: {body}")
            if e.code == 402:
                raise SystemExit("Stopping: HTTP 402 = no credit on this account. "
                                 "Add credit, or use a model whose name ends in :free.")
            if e.code in (400, 401, 403, 404):
                raise SystemExit(f"Stopping: HTTP {e.code} (bad key or model name).")
            wait = min(90, 10 * 2 ** i)
            print(f"  HTTP {e.code} (busy or rate-limited), waiting {wait}s")
            time.sleep(wait)
        except (urllib.error.URLError, KeyError, IndexError, TimeoutError) as e:
            print("  retry after error:", repr(e)[:120])
            time.sleep(10)
    return "ERROR"


def keep(raw):
    """Text saved to the file: whole reply if short, else first 140 + last 150 characters."""
    t = raw.replace("\n", " ")
    return t if len(t) <= 300 else t[:140] + " [...] " + t[-150:]


def parse_letter(text):
    """Return A/B/C/D only when the final answer is clear, else "" (counted as no answer).

    Clear means: the reply is just a letter (maybe bold or in brackets), or it states
    "Answer: X", or it marks one single letter in bold. Rambling text with no clear
    final choice is NOT guessed, so it can never be scored as right or wrong by luck.
    """
    t = text.strip()
    if t.startswith("[rescued]"):
        t = t[len("[rescued]"):].strip()
    m = re.fullmatch(r"\W*(?:(?:the\s+)?answer\s*(?:is)?\s*:?\s*)?\**\(?([ABCD])\)?\**\W*", t,
                     flags=re.I)
    if m:
        return m.group(1).upper()
    marks = list(re.finditer(r"\*\*\(?([ABCD])\)?[.)]?\*\*|[Aa]nswer(?:\s+is)?\s*:?\s*\**\(?([ABCD])\b", t))
    letters = {m.group(1) or m.group(2) for m in marks}
    # one single letter, and it is stated at the end of the reply (not mid-thought)
    if len(letters) == 1 and len(t) - marks[-1].end() <= 40:
        return letters.pop()
    return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider", required=True, choices=list(KEYS))
    ap.add_argument("--model", required=True)
    ap.add_argument("--mode", required=True, choices=["nastaliq", "roman"])
    ap.add_argument("--input", default="data/mcq_test_set.csv")
    ap.add_argument("--max-tokens", type=int, default=4096,
                    help="room for reasoning models to think before answering")
    ap.add_argument("--effort", default=None, choices=["low", "medium", "high", "none", "default", "off"],
                    help="reasoning effort for models that support it (optional)")
    ap.add_argument("--rescue", action="store_true",
                    help="if a reply has no clear letter, ask the model one follow-up for its "
                         "final letter (marked [rescued] in the file; report it in the paper)")
    ap.add_argument("--limit", type=int, default=0,
                    help="stop after this many NEW questions (0 = no limit); run again later to continue")
    ap.add_argument("--sleep", type=float, default=4.0, help="seconds between calls")
    a = ap.parse_args()

    key = os.environ.get(KEYS[a.provider])
    if not key:
        raise SystemExit(f"Set {KEYS[a.provider]} first (see the setup steps).")

    os.makedirs("results", exist_ok=True)
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", a.model)
    out_path = f"results/mcq_{safe}_{a.mode}.csv"

    with open(a.input, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    # Every row ever saved stays in the file. A stopped run can never delete finished rows.
    existing = {}
    if os.path.exists(out_path):
        with open(out_path, encoding="utf-8-sig", newline="") as f:
            existing = {r["id"]: r for r in csv.DictReader(f)}
    done = {i for i, r in existing.items()
            if r["raw_answer"] != "ERROR" and r["predicted"] != ""}

    fields = ["id", "mode", "model", "predicted", "correct", "is_correct", "raw_answer"]

    def save():
        with open(out_path, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            for k in sorted(existing, key=lambda x: int(x)):
                w.writerow(existing[k])

    new_done = 0
    for i, r in enumerate(rows, 1):
        if r["id"] in done:
            continue
        if a.limit and new_done >= a.limit:
            continue
        proverb = r["proverb_nastaliq"] if a.mode == "nastaliq" else r["transliteration"]
        prompt = PROMPT.format(proverb=proverb, a=r["option_a"], b=r["option_b"],
                               c=r["option_c"], d=r["option_d"])
        raw = ask_retry(a.provider, a.model, key, prompt, a.max_tokens, a.effort)
        if raw == "ERROR":
            print(f"{i}/{len(rows)} id={r['id']} FAILED, will retry on next run")
            continue
        pred = parse_letter(raw)
        if not pred and a.rescue:
            raw2 = ask_retry(a.provider, a.model, key, prompt, 100, a.effort,
                             turns=[("user", prompt), ("assistant", raw), ("user", FOLLOWUP)])
            p2 = parse_letter(raw2) if raw2 != "ERROR" else ""
            if p2:
                pred, raw = p2, "[rescued] " + p2
        existing[r["id"]] = {"id": r["id"], "mode": a.mode, "model": a.model,
                             "predicted": pred, "correct": r["correct_letter"],
                             "is_correct": int(pred == r["correct_letter"]),
                             "raw_answer": keep(raw)}
        new_done += 1
        print(f"{i}/{len(rows)} id={r['id']} pred={pred} correct={r['correct_letter']}")
        save()
        time.sleep(a.sleep)

    save()
    results = [existing[k] for k in existing]
    ok = sum(int(x["is_correct"]) for x in results)
    print(f"\n{a.model} [{a.mode}]: {ok}/{len(results)} = {100 * ok / len(results):.1f}%")
    print("Saved to", out_path)


if __name__ == "__main__":
    main()
