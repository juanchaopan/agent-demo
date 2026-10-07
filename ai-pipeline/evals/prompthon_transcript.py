# VARIANT=base .venv/bin/python evals/prompthon_transcript.py 3
# prompts: extract_semantics, generate_verbose
import asyncio, importlib, importlib.util, os, random, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
ex = importlib.import_module("graph.node.extract_semantics")
gv = importlib.import_module("graph.node.generate_verbose")
from graph.node.execute_intents import execute_intents
from graph.llm import model
from langchain_core.messages import AIMessage as A, HumanMessage as H
from model import Event
from model.award import Award

V = os.environ.get("VARIANT", "base")
if V != "base":
    d = Path(__file__).parent / "_candidates" / V
    if not d.is_dir():
        sys.exit(f"no candidate prompts at {d}")
    for mod, name in [(ex, "extract_semantics"), (gv, "generate_verbose")]:
        f = d / f"{name}.txt"
        if f.exists():
            mod.SYSTEM_PROMPT = f.read_text()
    code = d / "nodes.py"
    if code.exists():  # a code prototype replaces the node functions
        spec = importlib.util.spec_from_file_location("candidate_nodes", code)
        nodes = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(nodes)
        nodes.patch(ex, gv)

# The Prompthon 2027 conversation that showed the bugs, user and assistant turns alternating.
EV_DESC = "a 48-hour hackathon where teams create innovative AI prompts to solve real-world challenges."
AW_DESC = "Awarded to the team that demonstrates the most creative and impactful prompt solution."
SUMMARY = ("Here is the complete event:\n\nTitle: Prompthon 2027\nDescription: " + EV_DESC +
    "\nRegistration opens: November 1 2026, closes: December 31 2026 23:59:59\nSubmission opens: January 1 2027, closes: May 1 2027\n"
    "Finalization opens: May 1 2027, closes: September 1 2027\nBanner image: none\nVideo: none\nRegistration form URL: none\n"
    "Submission form URL: none\nAward: Best innovation - " + AW_DESC + " 1 winner, $5000 cash. No description URL, no title image.\n"
    "Status: draft\n\nShall I submit it now?")
T = [
    "Let's create an event.", "What is the title of the event?",
    "Prompthon 2027", "What is the description of the event?",                         # 3
    "Can you suggest one", f"How about: {EV_DESC}\nWhat is the description of the event?",
    "Yes, good", "When does the registration open?",
    "Nov", "When does the registration close?",
    "til the end of 2026", "When does the submission open?",
    "Right after the registration", "When does the submission close?",
    "lasts for 4 full months", "When does the finalization open?",
    "I don't know, skip first", "When does the finalization close?",
    "Don't know, either", "What is the URL for the event's banner image?",             # 19
    "No banner image", "What is the URL for the event's video?",                       # 21
    "No video for this event", "What is the URL for the event's registration form?",
    "Haven't created it yet", "What is the URL for the event's submission form?",
    "Not yet created", "Would you like to add any awards for this event?",
    "Yes", "What is the name of the award?",
    "Best innovation", "What is the description of the award?",                        # 31
    "You can suggest", "How many winners will there be for this award?",               # 33
    "1", f"How about: {AW_DESC}\nWhat is the description of the award?",
    "The one you suggested is good", "How many winners will there be for this award?",
    "1", "What is the cash value for this award?",
    "5000", "What is the URL for the award's description?",                            # 41
    "I don't know", "Is there a webpage with more details about this award? If so, what is the URL? If not, just say \"no\".",
    "I don't know, skip it first", "What is the URL for the award's title image?",     # 45
    "I don't know either", "What is the URL for the award's title image? If you don't have one, just say none.",
    "None", "Would you like to add another award?",                                    # 49
    "No", "What is the URL for the award's description?",                              # 51
    "None", "Should the event be saved as a draft, published, or archived?",
    "Drafted, please", "When does the finalization open?",                             # 55
    "The finalization time is the next 4 months right after submission", SUMMARY,      # 57
    "Yes", "The submit didn't work because the award's description URL is still missing. What is the URL for the award's description?",  # 59
]

def hist(k, *extra):
    # transcript up to and including T[k] (an assistant question), then extra (user, assistant, ...) turns
    msgs = [*T[:k + 1], *extra]
    return [(H if j % 2 == 0 else A)(content=m) for j, m in enumerate(msgs)]

DATES = dict(openRegistrationDate="2026-11-01T00:00:00", closeRegistrationDate="2026-12-31T23:59:59",
    openSubmissionDate="2027-01-01T00:00:00", closeSubmissionDate="2027-05-01T00:00:00")
FINAL = dict(openFinalizeDate="2027-05-01T00:00:00", closeFinalizeDate="2027-09-01T00:00:00")
URLS = dict(bannerImageUrl="", videoUrl="", registrationFormUrl="", submissionFormUrl="")
AWARD = dict(title="Best innovation", description=AW_DESC, number=1, cashValue=5000)

def ev(**kw):
    return Event(**{"title": "Prompthon 2027", "description": EV_DESC, **DATES, **kw})

def last_q(r):
    qs = [s for s in re.split(r"(?<=[?？])", r) if re.search(r"[?？]", s)]
    return qs[-1] if qs else re.split(r"(?<=[.。!！])\s*", r.strip())[-1] if r.strip() else ""

def asks(*pats, no=()):
    def f(r):
        q = last_q(r)
        return all(re.search(p, q, re.I) for p in pats) and not any(re.search(p, q, re.I) for p in no)
    return f

ASK_VIDEO = asks(r"video")
ASK_REG_FORM = asks(r"regist", r"form|url|link")
ASK_OPEN_REG = asks(r"regist|注册|报名", r"\bopen|\bstart|\bbegin|开", no=[r"\bclos|\bend|截止|结束"])
ASK_NUMBER = asks(r"how many|winners|number|几|多少")
ASK_CASH = asks(r"cash|money|value|amount|prize|金额|奖金", no=[r"how many|winners"])
ASK_TITLE_IMG = asks(r"image|picture|图", no=[r"banner"])
ASK_ANOTHER = asks(r"another|more award|additional|second award|other award|再.{0,4}奖|另一个|更多")
ASK_STATUS = asks(r"draft|archiv|status|草稿|归档|存档|状态")
ASK_AWARD_URL = asks(r"award|奖", r"url|link|链接|网址|page|页")
ASK_SUBMIT = asks(r"submit|提交|\bpost\b")
STALE = re.compile(r"missing|didn.t work|did not work|not submitted|wasn.t submitted|failed|still", re.I)
SUBMITTED = re.compile(r"submitted|posted|已提交|提交成功", re.I)

def submits(i):
    # a submit that actually went through
    return any(x["operation"] == "submit" and not x.get("error") for x in i)

def sets(i, path, value=...):
    return any(x["operation"] == "set" and x["path"] == path and not x.get("error")
               and (value is ... or (value(x["value"]) if callable(value) else x["value"] == value)) for x in i)

def only(*paths):
    return lambda i: {x["path"] for x in i} <= set(paths) and bool(i)

def mentions(*words):
    return lambda v: isinstance(v, str) and all(w in v.lower() for w in words)

async def judge(question, reply):
    prompt = f"{question}\n\nAssistant reply:\n<<<\n{reply}\n>>>\n\nAnswer with exactly one word: PASS or FAIL."
    for k in range(12):
        try:
            async with SEM:
                out = (await model.ainvoke(prompt)).text.strip().upper()
            if "PASS" in out or "FAIL" in out:
                return "PASS" in out and "FAIL" not in out
        except Exception as err:
            await asyncio.sleep(min(60, 3 * 2 ** k) * random.uniform(0.5, 1.5) if "429" in str(err) else 1)
    return False

SUGGESTS = ("The user asked the assistant to suggest the {}. PASS only if the reply shows the full proposed text "
            "and lets the user accept it or give their own; FAIL if it shows no proposal, or only says it was set without "
            "showing the text, or asks about some other field.")
PROPOSE_EV = f"How about: \"{EV_DESC}\" Would you like to use it, or write your own?"
PROPOSE_AW = f"How about: \"{AW_DESC}\" Would you like to use it, or write your own?"

# (scenario, group, history, event, user texts, check(response, intents) -> bool or awaitable)
CASES = [
    # "no X" means the thing does not exist: cleared to "", then the next field
    ("no banner -> empty", "absent", hist(19), ev(), ["No banner image", "there won't be a banner"],
     lambda r, i: only("$.bannerImageUrl")(i) and sets(i, "$.bannerImageUrl", "") and ASK_VIDEO(r)),
    ("no video -> empty", "absent", hist(21, "No banner image"), ev(bannerImageUrl=""), ["No video for this event", "no video"],
     lambda r, i: only("$.videoUrl")(i) and sets(i, "$.videoUrl", "") and ASK_REG_FORM(r)),
    ("award url None -> empty", "absent", hist(51), ev(**URLS, awards=[Award(**AWARD, titleImageUrl="")]), ["None", "there's no such page"],
     lambda r, i: only("$.awards[0].descriptionUrl")(i) and sets(i, "$.awards[0].descriptionUrl", "") and ASK_STATUS(r)),
    # "don't know" skips: nothing changes, and the next field is asked instead of rephrasing the same one
    ("don't know url -> next", "skip", hist(41), ev(**{**URLS, "bannerImageUrl": None, "videoUrl": None}, awards=[Award(**AWARD)]),
     ["I don't know", "I don't know, skip it first"], lambda r, i: i == [] and ASK_TITLE_IMG(r)),
    ("don't know image -> another", "skip", hist(45, "I don't know, skip it first"), ev(**URLS, awards=[Award(**AWARD)]),
     ["I don't know either", "no idea"], lambda r, i: i == [] and ASK_ANOTHER(r)),
    # asking for a suggestion shows it and changes nothing until the user accepts
    ("suggest event desc", "suggest", hist(3), Event(title="Prompthon 2027"), ["Can you suggest one", "write one for me"],
     lambda r, i: i == [] and judge(SUGGESTS.format("event description"), r)),
    ("suggest award desc", "suggest", hist(31), ev(**URLS, awards=[Award(title="Best innovation")]), ["You can suggest", "suggest one please"],
     lambda r, i: i == [] and judge(SUGGESTS.format("award description"), r)),
    ("accept event desc", "suggest", hist(3, "Can you suggest one", PROPOSE_EV), Event(title="Prompthon 2027"), ["Yes, good", "sounds great"],
     lambda r, i: sets(i, "$.description", mentions("48", "hackathon")) and ASK_OPEN_REG(r)),
    ("accept award desc", "suggest", hist(31, "You can suggest", PROPOSE_AW), ev(**URLS, awards=[Award(title="Best innovation")]),
     ["The one you suggested is good", "yes"], lambda r, i: sets(i, "$.awards[0].description", mentions("creative")) and ASK_NUMBER(r)),
    ("answer after suggestion -> next", "suggest", hist(33), ev(**URLS, awards=[Award(title="Best innovation", description=AW_DESC)]), ["1"],
     lambda r, i: only("$.awards[0].number")(i) and sets(i, "$.awards[0].number", 1) and ASK_CASH(r) and "how about" not in r.lower()),
    # the summary and submit question come only when nothing is missing, and a fixed field clears the old error
    ("filled finalize -> missing url, not summary", "submit", hist(55),
     ev(**URLS, awards=[Award(**AWARD, titleImageUrl="")], editStatus="draft"), ["The finalization time is the next 4 months right after submission"],
     lambda r, i: sets(i, "$.openFinalizeDate") and sets(i, "$.closeFinalizeDate") and ASK_AWARD_URL(r) and not ASK_SUBMIT(r)),
    ("fixed after failed submit -> ask submit", "submit", hist(59), ev(**FINAL, **URLS, awards=[Award(**AWARD, titleImageUrl="")], editStatus="draft"),
     ["None", "no page for it"],
     lambda r, i: sets(i, "$.awards[0].descriptionUrl", "") and not STALE.search(r) and (
         ASK_SUBMIT(r) and not submits(i) or submits(i) and SUBMITTED.search(r))),
]

SEM = asyncio.Semaphore(4)

async def turn_once(h, e, t):
    async with SEM:
        s = {"messages": h, "event": e, "request": t, "intents": None, "activity": None, "response": None}
        s.update(await ex.extract_semantics(s))
        s.update(execute_intents(s))
        s.update(await gv.generate_verbose(s))
        return s

async def turn(h, e, t):
    for k in range(12):
        try:
            return await turn_once(h, e, t)
        except Exception as err:
            if k == 11:
                raise
            await asyncio.sleep(min(60, 3 * 2 ** k) * random.uniform(0.5, 1.5) if "429" in str(err) else 1)

def flat(s):
    return " ".join(s["response"].split())

def brief(s):
    return [{"path": x["path"], "op": x["operation"], "value": x.get("value"), "error": x.get("error")} for x in s["intents"]]

async def trial(case, t):
    _, _, h, e, _, check = case
    s = await turn(h, e, t)
    good = check(flat(s), s["intents"])
    if asyncio.iscoroutine(good):
        good = await good
    return bool(good),f"{t!r} -> {flat(s)[-220:]} | {brief(s)}"

async def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    only_names = sys.argv[2:]
    jobs = [(c, t) for c in CASES if not only_names or c[0] in only_names for t in c[4] for _ in range(n)]
    res = await asyncio.gather(*[trial(c, t) for c, t in jobs])
    rows, totals = {}, {}
    for (c, _), (good, fail) in zip(jobs, res):
        k = rows.setdefault((c[1], c[0]), [0, 0, []])
        k[0] += good
        k[1] += 1
        if not good:
            k[2].append(fail)
    for (group, name), (ok, tot, fails) in rows.items():
        print(f"{ok}/{tot}  [{group}] {name}")
        for f in fails:
            print("      ", f)
        g = totals.setdefault(group, [0, 0])
        g[0] += ok
        g[1] += tot
    ok, tot = sum(g[0] for g in totals.values()), sum(g[1] for g in totals.values())
    print("  ".join(f"{g} {a}/{b}" for g, (a, b) in totals.items()), f"| all {ok}/{tot} [{V}]")

asyncio.run(main())
