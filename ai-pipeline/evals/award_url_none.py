# VARIANT=base .venv/bin/python evals/award_url_none.py 3
# prompts: extract_semantics, generate_verbose
import asyncio, importlib, importlib.util, os, random, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
ex = importlib.import_module("graph.node.extract_semantics")
gv = importlib.import_module("graph.node.generate_verbose")
from graph.node.execute_intents import execute_intents
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

# The second Prompthon 2027 conversation, user and assistant turns alternating.
EV_DESC = "A 48-hour prompt engineering hackathon where participants build AI-powered solutions."
AW_DESC = "For the most innovative AI solution."
Q_URL = "What is the URL for the award's description? (You can say none if there isn't one.)"
Q_IMG = "What is the URL for the award's title image? (You can say none if there isn't one.)"
T = [
    "Let's create an event.", "What is the title of the event?",
    "Prompthon 2027", "What is the description of the event?",
    "Can you suggest one", f'How about: "{EV_DESC}" Would you like to use it, or something else?',
    "Sounds good", "When does registration open?",
    "Nov", "When does registration close?",
    "By the end of 2026", "When does submission open?",
    "Right after the registrationd", "When does submission close?",
    "Lasts for 4 months", "When does finalization open?",
    "I don't know, let's skip this question for now", "When does finalization close?",
    "I don't know, either", "What is the URL for the event's banner image?",
    "We don't have such banner image", "What is the URL for the event's video?",
    "We don't have a video for this event", "What is the URL for the event's registration form?",
    "We haven't one", "What is the URL for the event's submission form?",
    "We don't have it", "Would you like to add any awards for this event?",
    "Yes", "What is the title of the award?",
    "Best innovation", "What is the description for the Best innovation award?",
    "Can you suggest one", 'How about: "An award for the most creative and impactful AI solution demonstrated during the hackathon." Would you like to use it, or something else?',
    "A shorter one", f'How about: "{AW_DESC}" Would you like to use it, or something else?',
    "OK", "How many winners will there be for this award?",
    "1", "What is the cash value for the Best innovation award?",
    "5000", Q_URL,                                                       # 41
    "I don't know", Q_IMG,                                              # 43
    "None", "Would you like to add another award?",                     # 45
    "None", "Should the event be saved as a draft, published, or archived?",
    "Draft", "When does finalization open?",
    "After the submission", "When does finalization close?",
    "August", Q_URL,                                                    # 53
    "None", Q_IMG,                                                      # 55
    "None", Q_URL,                                                      # 57
    "None", Q_IMG,                                                      # 59
]

def hist(k, *extra):
    # transcript up to and including T[k] (an assistant question), then extra (user, assistant, ...) turns
    msgs = [*T[:k + 1], *extra]
    return [(H if j % 2 == 0 else A)(content=m) for j, m in enumerate(msgs)]

DATES = dict(openRegistrationDate="2026-11-01T00:00:00", closeRegistrationDate="2026-12-31T23:59:59",
    openSubmissionDate="2027-01-01T00:00:00", closeSubmissionDate="2027-05-01T00:00:00")
FINAL = dict(openFinalizeDate="2027-05-01T00:00:00", closeFinalizeDate="2027-08-31T23:59:59")
URLS = dict(bannerImageUrl="", videoUrl="", registrationFormUrl="", submissionFormUrl="")
AWARD = dict(title="Best innovation", description=AW_DESC, number=1, cashValue=5000)

def ev(url=None, img=None, **kw):
    return Event(title="Prompthon 2027", description=EV_DESC, **DATES, **URLS,
                 awards=[Award(**AWARD, descriptionUrl=url, titleImageUrl=img)], **kw)

def last_q(r):
    qs = [s for s in re.split(r"(?<=[?？])", r) if re.search(r"[?？]", s)]
    return qs[-1] if qs else re.split(r"(?<=[.。!！])\s*", r.strip())[-1] if r.strip() else ""

def asks(*pats, no=()):
    def f(r):
        q = last_q(r)
        return all(re.search(p, q, re.I) for p in pats) and not any(re.search(p, q, re.I) for p in no)
    return f

ASK_URL = asks(r"descri", r"url|link|page")
ASK_IMG = asks(r"image|picture", no=[r"banner"])
ASK_ANOTHER = asks(r"another|more award|additional|second award|other award")
ASK_STATUS = asks(r"draft|archiv|status")
ASK_SUBMIT = asks(r"submit|\bpost\b|publish it")
URL, IMG = "$.awards[0].descriptionUrl", "$.awards[0].titleImageUrl"

def sets(i, path, value=...):
    return any(x["operation"] == "set" and x["path"] == path and not x.get("error")
               and (value is ... or x["value"] == value) for x in i)

def only(*paths):
    return lambda i: {x["path"] for x in i} <= set(paths) and bool(i)

NONE = ["None", "none", "N/A"]

# (scenario, group, history, event, user texts, check(response, intents))
CASES = [
    # 1. "None" to an award URL sets "", then the next question
    ("url None (first pass) -> empty", "none", hist(41), ev(), NONE,
     lambda r, i: only(URL)(i) and sets(i, URL, "") and ASK_IMG(r)),
    ("image None (first pass) -> empty", "none", hist(43), ev(), NONE,
     lambda r, i: only(IMG)(i) and sets(i, IMG, "") and ASK_ANOTHER(r)),
    ("url None (second pass) -> empty", "none", hist(53), ev(**FINAL, editStatus="draft"), NONE,
     lambda r, i: only(URL)(i) and sets(i, URL, "") and ASK_IMG(r)),
    ("url None (last missing) -> summary", "none", hist(57), ev(img="", **FINAL, editStatus="draft"), ["None", "there isn't one"],
     lambda r, i: only(URL)(i) and sets(i, URL, "") and ASK_SUBMIT(r)),
    # 2. a field that is "" is never asked again
    ("image None, url still missing -> url", "next", hist(55), ev(**FINAL, editStatus="draft"), ["None", "no image"],
     # also setting the earlier, dropped "None" for the URL is fine, as long as the reply follows the result
     lambda r, i: only(IMG, URL)(i) and sets(i, IMG, "") and (ASK_SUBMIT(r) if sets(i, URL, "") else ASK_URL(r) or ASK_ANOTHER(r))),
    ("url skipped, image already empty -> not image", "next", hist(57), ev(img="", **FINAL, editStatus="draft"), ["I don't know", "skip it"],
     lambda r, i: i == [] and not ASK_IMG(r) and not ASK_SUBMIT(r)),
    # 3. no summary or submit question while a field is null
    ("image already empty, url missing -> url", "next", hist(59), ev(img="", **FINAL, editStatus="draft"), ["None"],
     # after the last award's title image, asking about another award is also fine
     lambda r, i: not ASK_SUBMIT(r) and (ASK_URL(r) or ASK_ANOTHER(r))),
    ("finalize done -> url, not summary", "next", hist(51), ev(img="", editStatus="draft", openFinalizeDate=FINAL["openFinalizeDate"]), ["August"],
     lambda r, i: sets(i, "$.closeFinalizeDate") and ASK_URL(r) and not ASK_SUBMIT(r)),
    # declining another award with "None" changes nothing
    ("another award: None -> status", "next", hist(45), ev(img=""), ["None"],
     lambda r, i: i == [] and ASK_STATUS(r)),
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
    return bool(check(flat(s), s["intents"])), f"{t!r} -> {flat(s)[-200:]} | {brief(s)}"

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
