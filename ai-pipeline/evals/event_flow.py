# VARIANT=base .venv/bin/python evals/event_flow.py 4
# prompts: extract_semantics, generate_verbose
import asyncio, importlib, importlib.util, os, re, sys
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

DESC = "FIRA 2027 is a global tech conference and expo with keynotes and a large expo hall."
DATES = dict(openRegistrationDate="2026-11-01T00:00:00", closeRegistrationDate="2026-12-31T00:00:00",
    openSubmissionDate="2027-01-01T00:00:00", closeSubmissionDate="2027-04-30T00:00:00",
    openFinalizeDate="2027-05-01T00:00:00", closeFinalizeDate="2027-08-31T00:00:00")
URLS = dict(bannerImageUrl="", videoUrl="", registrationFormUrl="", submissionFormUrl="")
HEAD = dict(title="FIRA 2027", description=DESC)
A1 = dict(title="Best Demo", description="Best live demo of the year", number=1, cashValue=1000, descriptionUrl="")
A2 = dict(title="Best Paper", description="Best written paper overall", number=2, cashValue=500, descriptionUrl="")
NEW_AWARD = dict(title=None, description=None, number=None, cashValue=None, descriptionUrl=None, titleImageUrl=None)

def ev(**kw):
    return Event(**{**HEAD, **DATES, **URLS, **kw})

def last_q(r):
    qs = [s for s in re.split(r"(?<=[?？])", r) if re.search(r"[?？]", s)]
    return qs[-1] if qs else re.split(r"(?<=[.。!！])\s*", r.strip())[-1] if r.strip() else ""

def asks(*pats, no=()):
    def f(r):
        q = last_q(r)
        return all(re.search(p, q, re.I) for p in pats) and not any(re.search(p, q, re.I) for p in no)
    return f

ASK_DESC = asks(r"descri|描述", no=[r"award|奖"])
ASK_OPEN_REG = asks(r"regist|注册|报名", r"\bopen|\bstart|\bbegin|开", no=[r"\bclos|\bend|截止|结束"])
ASK_CLOSE_REG = asks(r"regist|注册|报名", r"\bclos|\bend|截止|结束")
ASK_OPEN_SUB = asks(r"submission|提交", r"\bopen|\bstart|\bbegin|开", no=[r"\bclos|\bend"])
ASK_TITLE = asks(r"title|name|标题|名称", no=[r"award|奖"])
ASK_AWARD_NUMBER = asks(r"how many|winners|number|几|多少")
ASK_AWARD_NAME = asks(r"award|prize|奖", r"name|title|call|名称|名字|标题|叫")
ASK_ANOTHER = asks(r"another|more award|additional|second award|other award|再.{0,4}奖|另一个|更多")
ASK_STATUS = asks(r"draft|archiv|status|草稿|归档|存档|状态")
ASK_SUBMIT = asks(r"submit|提交|\bpost\b", no=[r"final changes|最终修改"])
ASK_BANNER = asks(r"banner|横幅")
ASK_AWARD_URL = asks(r"award|奖", r"url|link|链接|网址")
YESNO = re.compile(r"^\W*(could|can|would|do|does|will|is there|are there|have you|did)\b", re.I)

def WH(r):
    return not YESNO.search(last_q(r).split(". ")[-1].strip())

SUBMITTED = re.compile(r"submitted|posted|已提交|提交成功|成功提交|已发布", re.I)

def sets(i, path, value=...):
    return any(x["operation"] == "set" and x["path"] == path and (value is ... or x["value"] == value) for x in i)

def ops(i):
    return [x["operation"] for x in i]

def no_submit(r, i):
    return "submit" not in ops(i) and not SUBMITTED.search(r)

def submitted_ok(r, i):
    return "submit" in ops(i) and not any(x.get("error") for x in i) and bool(SUBMITTED.search(r)) and DESC[:20] not in r

def adds_award(i):
    return any(x["operation"] == "add" and x["path"] == "$.awards" for x in i)

def only(*paths):
    return lambda i: {x["path"] for x in i} <= set(paths) and bool(i)

Q_IMG = "Could you share the URL for the award's title image?"
Q_ANOTHER = "Would you like to add another award?"
Q_AWARDS = "Would you like to add any awards for this event?"
Q_STATUS = "Should the event be saved as a draft, published, or archived?"
AFTER_IMG = ["https://x.io/demo.png", "we don't have an image for it", "skip that one", "没有图片"]

# (scenario, group, history, event, user texts, check(response, intents))
CASES = [
    ("answer title", "regression", [A(content="What is the title of the event?")], Event(), ["it's called RoboCup Asia 2027"],
     lambda r, i: sets(i, "$.title") and ASK_DESC(r)),
    ("skip a date", "regression", [A(content="When does the registration open?")], Event(**HEAD), ["not sure yet, skip", "I'll decide later"],
     lambda r, i: i == [] and ASK_CLOSE_REG(r)),
    ("question", "regression", [A(content="When does the registration open?")], Event(**HEAD), ["what is registration for?"],
     lambda r, i: i == [] and ASK_OPEN_REG(r)),
    ("period", "regression", [A(content="When does the registration open?")], Event(**HEAD), ["Nov 1 to Dec 15 this year"],
     lambda r, i: sets(i, "$.openRegistrationDate") and sets(i, "$.closeRegistrationDate") and ASK_OPEN_SUB(r)),
    ("rejected", "regression", [A(content="When does the registration close?")], Event(**HEAD, openRegistrationDate="2026-11-01T00:00:00"),
     ["October 1, 2026"], lambda r, i: any(x.get("error") for x in i) and ASK_CLOSE_REG(r)),
    ("jump back", "regression", [A(content="Could you share the URL for the event's video?")], ev(videoUrl=None),
     ["hold on, I want to change the event title first"], lambda r, i: i == [] and ASK_TITLE(r)),
    ("no awards", "regression", [A(content=Q_AWARDS)], ev(), ["no prizes this time", "nope"],
     lambda r, i: sets(i, "$.awards", []) and not adds_award(i) and ASK_STATUS(r)),
    ("yes awards", "regression", [A(content=Q_AWARDS)], ev(), ["yes", "sure, we have one"],
     lambda r, i: adds_award(i) and ASK_AWARD_NAME(r)),
    ("award field", "regression", [A(content="Please provide a brief description of the award.")],
     ev(awards=[Award(title="Most Creative")]), ["given to the most creative robot design"],
     lambda r, i: sets(i, "$.awards[0].description") and ASK_AWARD_NUMBER(r)),
    ("2nd award field", "regression", [A(content=Q_IMG)], ev(awards=[Award(**A1, titleImageUrl=""), Award(**A2)]),
     ["https://x.io/paper.png", "none"], lambda r, i: only("$.awards[1].titleImageUrl")(i) and ASK_ANOTHER(r)),
    ("no to banner", "regression", [A(content="Could you share the URL for the event's banner image?")],
     ev(bannerImageUrl=None, awards=[Award(**A1, titleImageUrl="")], editStatus="draft"), ["no", "nope"], no_submit),
    ("wh: banner", "optional", [A(content="When does the finalization close?")], ev(closeFinalizeDate=None, bannerImageUrl=None),
     ["end of August 2027"], lambda r, i: ASK_BANNER(r) and WH(r)),
    ("wh: award url", "optional", [A(content="What is the monetary value of the award?")], ev(awards=[Award(title="Best Demo", description="Best live demo of the year", number=1)]),
     ["$1000"], lambda r, i: ASK_AWARD_URL(r) and WH(r)),
    ("none -> empty", "optional", [A(content="What is the URL for the event's banner image?")], ev(bannerImageUrl=None),
     ["no", "we don't have one", "没有"], lambda r, i: only("$.bannerImageUrl")(i) and sets(i, "$.bannerImageUrl", "")),
    ("later -> nothing", "optional", [A(content="What is the URL for the event's banner image?")], ev(bannerImageUrl=None),
     ["skip for now", "I'll send it later"], lambda r, i: i == []),
    ("last award -> another", "award", [A(content=Q_IMG)], ev(awards=[Award(**A1)]), AFTER_IMG,
     lambda r, i: ASK_ANOTHER(r)),
    ("last award -> another (status set)", "award", [A(content=Q_IMG)], ev(awards=[Award(**A1)], editStatus="draft"),
     ["https://x.io/demo.png", "no image"], lambda r, i: ASK_ANOTHER(r) and no_submit(r, i)),
    ("decline another -> status", "award", [A(content=Q_ANOTHER)], ev(awards=[Award(**A1, titleImageUrl="")]),
     ["nah, one is enough", "就这一个", "no more awards"], lambda r, i: i == [] and ASK_STATUS(r)),
    ("decline another -> submit q", "award", [A(content=Q_ANOTHER)], ev(awards=[Award(**A1, titleImageUrl="")], editStatus="draft"),
     ["no thanks", "that's all for awards"], lambda r, i: no_submit(r, i) and ASK_SUBMIT(r)),
    ("accept another", "award", [A(content=Q_ANOTHER)], ev(awards=[Award(**A1, titleImageUrl="")]),
     ["sure, add one more", "再加一个", "yes"], lambda r, i: adds_award(i) and ASK_AWARD_NAME(r)),
]

YES = ["yes", "sure, go ahead", "好的", "yep, do it", "ok"]
NO = ["not yet", "no", "先别"]
CHANGE = ["no, change the cash value to 2000", "wait, the title should be FIRA Summit 2027"]
FINAL = [
    ("yes -> submit", YES, submitted_ok),
    ("no -> no submit", NO, no_submit),
    ("change -> no submit", CHANGE, lambda r, i: no_submit(r, i) and "set" in ops(i)),
]
EARLIER = [A(content=Q_IMG), H(content="none"), A(content=Q_ANOTHER), H(content="no"), A(content=Q_STATUS)]

SEM = asyncio.Semaphore(4)

async def turn_once(h, e, t):
    async with SEM:
        s = {"messages": h, "event": e, "request": t, "intents": None, "activity": None, "response": None}
        s.update(await ex.extract_semantics(s))
        s.update(execute_intents(s))
        s.update(await gv.generate_verbose(s))
        return s

async def turn(h, e, t):
    for k in range(8):
        try:
            return await turn_once(h, e, t)
        except Exception as err:
            if k == 7:
                raise
            await asyncio.sleep(2 + 2 * k if "429" in str(err) else 0)

def flat(s):
    return " ".join(s["response"].split())

def brief(s):
    return [{"path": x["path"], "op": x["operation"], "value": x.get("value"), "error": x.get("error")} for x in s["intents"]]

async def case_trial(case, t):
    _, _, h, e, _, check = case
    s = await turn(h, e, t)
    return check(flat(s), s["intents"]), f"{t!r} -> {flat(s)[-170:]} | {brief(s)}"

async def final_trial(t, check):
    s1 = await turn(EARLIER, ev(awards=[Award(**A1, titleImageUrl="")]), "Draft")
    s2 = await turn([*EARLIER, H(content="Draft"), A(content=s1["response"])], s1["event"], t)
    return (ASK_SUBMIT(flat(s1)), f"-> {flat(s1)[-170:]}"), \
        (check(flat(s2), s2["intents"]), f"{t!r} -> {flat(s2)[:170]} | {brief(s2)}  (asked: {last_q(flat(s1))[-80:]})")

async def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    case_jobs = [(c, t) for c in CASES for t in c[4] for _ in range(n)]
    final_jobs = [(name, t, check) for name, ts, check in FINAL for t in ts for _ in range(n)]
    case_res, final_res = await asyncio.gather(
        asyncio.gather(*[case_trial(c, t) for c, t in case_jobs]),
        asyncio.gather(*[final_trial(t, check) for _, t, check in final_jobs]))
    rows = {}

    def add(name, group, good, fail):
        k = rows.setdefault((group, name), [0, 0, []])
        k[0] += good
        k[1] += 1
        if not good:
            k[2].append(fail)

    for (c, _), (good, fail) in zip(case_jobs, case_res):
        add(c[0], c[1], good, fail)
    for (name, _, _), (step1, step2) in zip(final_jobs, final_res):
        add("final: asks to submit", "submit", *step1)
        add(f"final: {name}", "submit", *step2)
    totals = {}
    for (group, name), (ok, tot, fails) in sorted(rows.items(), key=lambda kv: kv[0][0]):
        print(f"{ok}/{tot}  [{group}] {name}")
        for f in fails:
            print("      ", f)
        g = totals.setdefault(group, [0, 0])
        g[0] += ok
        g[1] += tot
    print("  ".join(f"{g} {ok}/{tot}" for g, (ok, tot) in totals.items()), f"[{V}]")

asyncio.run(main())
