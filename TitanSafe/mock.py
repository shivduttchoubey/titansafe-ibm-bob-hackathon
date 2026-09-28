"""Deterministic mock social-media datasets.

Dataset A — default (seed=7):
  3 coordinated campaigns (incitement, targeted-harassment, misinformation) hidden in organic
  noise, plus deliberate false-positive traps (trending-but-organic hashtag, friendly fan
  mentions).

Dataset B — "election_disinfo" (seed=42):
  Two misinformation campaigns around a fictional state election (fake voting machine tampering
  claim + voter-suppression rumour) mixed with genuine campaign chatter.

Dataset C — "communal_riot" (seed=99):
  One severe imminent-incitement cluster targeting a specific locality, one rumour campaign
  stoking communal tensions, and organic community posts.

Dataset D — "journalist_doxxing" (seed=13):
  Targeted-harassment campaign against a freelance journalist with explicit phone/address
  sharing, plus a coordinated brigading attempt, buried in celebrity fan noise.

All names, places, phone numbers and organisations are fictional.
"""
from __future__ import annotations
import datetime as dt, random, re
from dataclasses import dataclass

BASE = dt.datetime(2026, 9, 26, 18, 0, tzinfo=dt.timezone.utc)
HASH = re.compile(r"#(\w+)")
MENT = re.compile(r"@(\w+)")

@dataclass
class Post:
    post_id: str; user_id: str; handle: str; account_created: str; ts: str
    text: str; followers: int; region: str
    phone_on_file: str  # platform-held; NEVER disclosed by the abstraction layer

    @property
    def hashtags(self): return [h.lower() for h in HASH.findall(self.text)]
    @property
    def mentions(self): return [m.lower() for m in MENT.findall(self.text)]
    @property
    def dt(self): return dt.datetime.fromisoformat(self.ts)
    @property
    def created_dt(self): return dt.datetime.fromisoformat(self.account_created)


# ─── Dataset A: default ──────────────────────────────────────────────────────

INC = ["Time to teach them a lesson. Gather at {p} tomorrow {t}, bring sticks. #StandUpNow #ShutItDown",
       "Everyone come to {p} tomorrow {t}. Bring sticks, we will teach them a lesson! #StandUpNow #ShutItDown",
       "They must pay. Gather {p} {t} tomorrow, bring sticks and finish this. #StandUpNow #ShutItDown"]
HAR = ["@priya_reporter we know where you live. Stop writing or your family will pay. #ExposePriya",
       "@priya_reporter you will be found, watch your back. Call her: {ph} #ExposePriya",
       "Everyone report and hound @priya_reporter, she deserves what is coming. #ExposePriya"]
MIS = ["BREAKING: water supply in {c} poisoned by outsiders, 40 hospitalised. Forward to all before it is deleted! #WaterAlert",
       "URGENT forward to all: {c} water poisoned by outsiders, many hospitalised. Share before it is deleted #WaterAlert"]
ORG = [
    "Loving the new metro line, so much faster.", "Anyone tried the biryani at the corner place? Worth it.",
    "Exam results are out, fingers crossed!", "Traffic near the flyover is terrible today #traffic",
    "Rain again. Chai and a good book.", "Our society Diwali cleanup drive is this Sunday #community",
    "Recommend a good physiotherapist in Gandhinagar?", "Just finished a 10k run, legs are jelly #running",
    "The new season of that thriller is brilliant", "Power cut again in our block, third time this week",
    "Book fair opens next week at the ground #books", "Free coding workshop for students on Saturday #learn",
    "The mango shake at the new place is unbeatable #food", "Finally got a window seat on the bus today, small wins",
    "Missed the local train by 30 seconds, story of my life", "Anyone watching the new web series? Worth it?",
    "Water tanker did not come again today #WaterCrisis", "Stray dog near the park needs help, someone please",
    "Solar panels installed on our terrace, saving ₹800/month #GreenEnergy", "School admission forms out already?",
    "Our mohalla committee planted 50 saplings this morning #GreenIndia", "Auto wala took a wrong route, charged double",
    "New footpath tiles already broken after one week #CivicFail", "Polling booth was surprisingly well organised",
    "The municipal corporation app actually worked today, miracle", "Dahi wada stall near the stadium is legendary",
    "My dog learned a new trick, proud parent moment #dogs", "Monsoon drains are blocked again near sector 4",
    "Evening walk along the river is the best therapy", "Hospital waiting time was 3 hours, system needs work",
    "Volunteer drive for flood relief, please join #FloodRelief", "Local market prices up again this week",
    "Power backup failed during the exam, nightmare fuel", "New bus route connecting our area, finally! #Transport",
    "Found a brilliant secondhand bookshop near the old market", "Heritage walk this Sunday, highly recommend #Heritage",
    "Kids cricket tournament in the colony, so much energy!", "Monsoon brings out the best chai weather #chai",
    "Garbage collected on time for once, appreciate it #Cleanliness", "Night market opens this weekend #shopping",
    "My grandmother voted today at 82, absolute legend", "Pothole on the main road is back after 2 weeks",
    "Street light outside our lane has been broken for a month", "Cycling track inauguration tomorrow #cycling",
    "Had the best gola in years near the old fort area", "Cultural fest at the university was amazing",
    "Train was on time today — historic! #IndianRailways", "Smart city project hoarding went up, work yet to start",
    "Local library getting a digital reading section #literacy", "Blood donation camp at the ground Sunday 9am",
    "Ration shop out of stock again this month", "New hospital OPD timings updated, check before you go",
    "Neighbourhood WhatsApp group is a chaos of good morning messages", "WiFi calling finally works on the metro",
    "School kids cleaning the beach is the kind of news I need", "Diwali bonus came in, treating myself to biryani",
]
CRIC = [
    "What a match #CricketFinal", "Unbelievable last over! #CricketFinal",
    "Still shaking after that finish #CricketFinal", "Best final in years #CricketFinal",
    "My heart cannot take this #CricketFinal", "Captain played a blinder #CricketFinal",
    "That last wicket was pure magic #CricketFinal", "Commentators losing their voice #CricketFinal",
    "Watching with the whole family, pure joy #CricketFinal", "Stadium atmosphere must be insane right now #CricketFinal",
]


def _phone(r): return "+91 " + str(r.randint(6, 9)) + "".join(str(r.randint(0, 9)) for _ in range(9))


def generate(seed: int = 7):
    r = random.Random(seed); posts = []; n = [0]
    def mk(kind, text_fn, age_days, followers, minute):
        n[0] += 1; uid = f"u{kind}{n[0]:04d}"
        created = BASE - dt.timedelta(days=age_days, hours=r.randint(0, 23))
        handle = f"{r.choice(['true','real','proud','voice','daily','just'])}_{r.choice(['citizen','patriot','user','one'])}{r.randint(10,999)}"
        ts = BASE + dt.timedelta(minutes=minute, seconds=r.randint(0, 59))
        posts.append(Post(f"p{n[0]:05d}", uid, handle, created.isoformat(), ts.isoformat(),
                          text_fn(), followers, r.choice(["GJ", "MH", "KL", "DL", "UP", "RJ"]), _phone(r)))
    for _ in range(80):   # incitement cluster — scaled up
        mk("c", lambda: r.choice(INC).format(p=r.choice(["Sector 9 market","Gandhi Chowk","Bus Stand Road"]),
           t=r.choice(["6pm", "6 pm", "at 6pm", "tonight 6"])),
           r.uniform(1, 9), r.randint(0, 40), r.uniform(0, 11))
    for _ in range(45):   # harassment cluster — scaled up
        mk("h", lambda: r.choice(HAR).format(ph="+91 9876501234"), r.uniform(2, 20), r.randint(0, 60), r.uniform(60, 110))
    for _ in range(55):   # misinformation cluster — scaled up
        mk("m", lambda: r.choice(MIS).format(c=r.choice(["Ward 4","Ward 7","Old Town"])),
           r.uniform(1, 12), r.randint(0, 45), r.uniform(120, 145))
    for _ in range(780):  # organic noise — scaled to dominate realistically
        mk("o", lambda: r.choice(ORG), r.uniform(200, 3000), r.randint(100, 5000), r.uniform(-480, 480))
    for i in range(55):   # organic trend trap: same hashtag, different text, same time
        mk("k", lambda i=i: CRIC[i % len(CRIC)] + ("!" * (i % 3)) + f" #{r.choice(['blue','india','cricket'])}",
           r.uniform(300, 2500), r.randint(80, 4000), r.uniform(200, 215))
    for _ in range(20):   # organic mention trap: many fans, one friendly target
        mk("f", lambda: r.choice(["Congrats @cric_official!", "Well played @cric_official, proud of you",
                                  "@cric_official what a captain", "Incredible innings @cric_official!"]),
           r.uniform(300, 2500), r.randint(80, 4000), r.uniform(202, 214))
    posts.sort(key=lambda p: p.ts)
    return posts


# ─── Dataset B: election_disinfo ─────────────────────────────────────────────

_ELEC_BASE = dt.datetime(2027, 3, 14, 10, 0, tzinfo=dt.timezone.utc)   # polling day

_EVM_TAMPER = [
    "BREAKING: EVMs in Booth {b} District {d} pre-loaded! Our observer saw it. Forward before deleted! #EVMFraud #VoteRigged",
    "URGENT: Voting machines in {d} already showing wrong results according to sources inside booth {b}. Share everywhere #EVMFraud",
    "They are stealing the election in {d}! Booth {b} machines rigged. Forward to all before it is deleted! #EVMFraud #VoteRigged",
    "Official whistleblower says EVM booth {b} {d} is compromised. Tell everyone, forward now #VoteRigged #EVMFraud",
]
_VOTER_SUPP = [
    "WARNING: If you have ration card type B, you CANNOT vote today in {d}. New rule issued quietly. Share to inform! #DontVote",
    "ALERT sent by {d} collector office: Voters born before 1980 must show Aadhaar + one more ID or be turned away. Forward! #DontVote",
    "People being turned away at booths in {d} without new voter slip. Old slips invalid today! Pass this on #DontVote",
]
_ELEC_GENUINE = [
    "Voted! Feeling proud. #VotingDay #Election2027", "Long queue at our booth but moving fast #Election2027",
    "My mom voted for the first time at 74 #Election2027 #ProudMoment", "Booth officers are very professional #VotingDay",
    "Expecting a surprise result this time #Election2027", "Every vote counts, go vote! #VotingDay",
    "Booth 42 in Rampur is empty, come vote #Election2027", "Snacks stall outside my booth, nice touch #VotingDay",
    "Result day tension is already building #Election2027", "Democracy in action #VotingDay",
    "Polling percentage looking good in my area #Election2027", "Political analysts getting it wrong again as usual #Election2027",
    "Excited to cast my first vote today! #Election2027", "Entire family voted together #VotingDay #Election2027",
    "Ink on the finger, duty done #VotingDay", "Security arrangements look solid at the booths #Election2027",
    "Voter turnout is looking high this time #Election2027", "The EVM process was smooth and fast #VotingDay",
    "Waited 40 minutes but totally worth it #VotingDay #Election2027", "Mobile phones not allowed inside booth, as expected",
    "Helping elderly neighbours get to the booth #VotingDay #Community", "Live updates on news channels all day #Election2027",
    "Candidate banners everywhere but silence zone respected #Election2027", "Hoping for stability and good governance #Election2027",
    "Women voter turnout this time is impressive #Election2027", "College students voting in large numbers #YouthVotes",
    "Exit polls starting to come out #Election2027", "Counting day excitement is going to be intense #Election2027",
    "My area booth officer was super helpful #VotingDay", "First time voter jitters are real #Election2027 #FirstVote",
]
_ELEC_CELEB = [
    "Voted for the first time, feels amazing! #VotingDay", "Make your voice count! #Election2027",
    "Booth selfie tradition continues #VotingDay", "Change is coming #Election2027",
    "So happy to see young voters in line #VotingDay", "This election will be historic #Election2027",
    "My vote, my right, my pride #VotingDay", "Go vote before it gets too hot outside #Election2027",
    "Democracy is a privilege, use it #VotingDay", "Finger ink is the best accessory today #Election2027",
]


def generate_election_disinfo(seed: int = 42):
    """Dataset B — election misinformation + voter-suppression rumours. 1000+ users."""
    r = random.Random(seed); posts = []; n = [0]
    base = _ELEC_BASE

    def mk(kind, text_fn, age_days, followers, minute):
        n[0] += 1; uid = f"u{kind}{n[0]:04d}"
        created = base - dt.timedelta(days=age_days, hours=r.randint(0, 23))
        handle = f"{r.choice(['alert','truth','watch','real','expose'])}_{r.choice(['voter','citizen','desk','news','eye'])}{r.randint(10,999)}"
        ts = base + dt.timedelta(minutes=minute, seconds=r.randint(0, 59))
        posts.append(Post(f"p{n[0]:05d}", uid, handle, created.isoformat(), ts.isoformat(),
                          text_fn(), followers, r.choice(["UP", "MP", "RJ", "BR", "JH", "UK"]), _phone(r)))

    districts = ["Lakhanpur", "Devnagar", "Rampura", "Sultanpur", "Chandpur",
                 "Noorpur", "Bhimtal", "Vikaspur", "Krishnanagar", "Gomtinagar"]
    booths    = ["12", "24", "7", "33", "45", "18", "62", "91", "3", "57"]

    # Campaign 1: EVM-tampering misinformation (80 accounts)
    for _ in range(80):
        d = r.choice(districts); b = r.choice(booths)
        mk("e", lambda d=d, b=b: r.choice(_EVM_TAMPER).format(d=d, b=b),
           r.uniform(1, 8), r.randint(0, 35), r.uniform(0, 14))

    # Campaign 2: voter-suppression rumour (60 accounts)
    for _ in range(60):
        d = r.choice(districts)
        mk("s", lambda d=d: r.choice(_VOTER_SUPP).format(d=d),
           r.uniform(2, 15), r.randint(0, 50), r.uniform(70, 90))

    # Organic election chatter — scaled to 800
    for _ in range(800):
        mk("o", lambda: r.choice(_ELEC_GENUINE), r.uniform(200, 3000), r.randint(80, 6000), r.uniform(-300, 300))

    # Organic trend trap: celebrity endorsements / selfies (benign same-hashtag burst)
    for i in range(95):
        mk("c", lambda i=i: _ELEC_CELEB[i % len(_ELEC_CELEB)] + ("!" * (i % 2)),
           r.uniform(400, 3000), r.randint(200, 8000), r.uniform(180, 200))

    posts.sort(key=lambda p: p.ts)
    return posts


# ─── Dataset C: communal_riot ─────────────────────────────────────────────────

_RIOT_BASE = dt.datetime(2027, 1, 5, 16, 0, tzinfo=dt.timezone.utc)   # Friday afternoon

_RIOT_INC = [
    "They are attacking our brothers in {loc}! Everyone gather at {gate} {t} bring sticks we will teach them. #RiseUp #ProtectOurPeople",
    "Our people being attacked at {loc}. Come to {gate} {t} with sticks and finish this once and for all. #RiseUp",
    "Enough is enough. Gather {gate} tonight {t}. Bring weapons and settle this. {loc} attack is unforgivable. #RiseUp #ProtectOurPeople",
    "Alert brothers: Assembly at {gate} {t}. Bring sticks. They attacked {loc} we will not sit quiet. #RiseUp",
]
_RIOT_MIS = [
    "BREAKING: outsiders attacked temple in {loc}. 10 injured. Police not responding. Share before deleted! #SaveUs #CommunalAlert",
    "URGENT: {community} mob vandalised {loc} shrine. 6 arrested but released. Forward to all #CommunalAlert",
    "Rumour or truth? Sources say {loc} area being targeted today. Stay alert. #CommunalAlert #SaveUs",
    "Violence erupting in {loc}. Outsiders responsible. Share before government suppresses this. #CommunalAlert",
]
_RIOT_ORG = [
    "Republic Day preparations at our school looking great! #RepublicDay", "New park opened in our ward, finally! #LocalNews",
    "Anyone know a good tuition teacher for 10th class in Vyas Nagar?", "Great turnout at the blood donation camp today",
    "Traffic signal at the crossing is still broken, please fix it #CivicIssue", "Congratulations to our colony cricket team #cricket",
    "Power restored after 4 hours, relief! #electricity", "Nice weather today, perfect for a morning walk",
    "Local market closed today for maintenance", "Volunteers needed for community garden this Sunday #community",
    "New library opening in sector 7 next week #books", "Speed breakers needed near the school #safety",
    "Annual sports day at the government school was wonderful", "Colony meeting about streetlight repair tomorrow evening",
    "Ration card renewal camp at ward office this Saturday", "Auto-rickshaw stand getting a shade canopy, finally",
    "Municipal water supply timing changed, check notices #water", "Diwali mela at the ground, entry free #festival",
    "New health centre opening in our ward this month #health", "Women self-help group fair tomorrow at community hall",
    "Our lane adopted by NCC cadets for cleanliness drive", "Free eye-check camp at the dispensary Wednesday",
    "Noise complaint about the loudspeaker at night, anyone else?", "Construction debris blocking the footpath again",
    "School uniform distribution starting next week #education", "Friendly match between ward 7 and ward 11 #sports",
]


def generate_communal_riot(seed: int = 99):
    """Dataset C — imminent incitement + communal misinformation. 1000+ users."""
    r = random.Random(seed); posts = []; n = [0]
    base = _RIOT_BASE

    def mk(kind, text_fn, age_days, followers, minute):
        n[0] += 1; uid = f"u{kind}{n[0]:04d}"
        created = base - dt.timedelta(days=age_days, hours=r.randint(0, 23))
        handle = f"{r.choice(['voice','protect','truth','guard','pride'])}_{r.choice(['warrior','sena','front','desk','citizen'])}{r.randint(10,999)}"
        ts = base + dt.timedelta(minutes=minute, seconds=r.randint(0, 59))
        posts.append(Post(f"p{n[0]:05d}", uid, handle, created.isoformat(), ts.isoformat(),
                          text_fn(), followers, r.choice(["UP", "MH", "MP", "RJ", "HR", "DL"]), _phone(r)))

    locs  = ["Haji Colony", "Rampur Chowk", "Old City Market", "Sector 11",
             "Noor Mohalla", "Azad Nagar Crossing", "Civil Lines Chowk"]
    gates = ["Lal Darwaza", "Main Chowk", "Bus Stand", "Tower Circle",
             "City Gate", "Station Road Junction"]
    times = ["7pm", "8pm", "at 7 pm", "tonight 7", "at 8 tonight", "7 baje"]
    comms = ["outsider", "minority group", "unknown group", "outsider elements"]

    # Campaign 1: imminent incitement (100 accounts, very tight burst)
    for _ in range(100):
        loc = r.choice(locs); gate = r.choice(gates); t = r.choice(times)
        mk("i", lambda loc=loc, gate=gate, t=t: r.choice(_RIOT_INC).format(loc=loc, gate=gate, t=t),
           r.uniform(1, 7), r.randint(0, 30), r.uniform(0, 9))

    # Campaign 2: communal misinformation (70 accounts)
    for _ in range(70):
        loc = r.choice(locs); community = r.choice(comms)
        mk("m", lambda loc=loc, community=community: r.choice(_RIOT_MIS).format(loc=loc, community=community),
           r.uniform(1, 10), r.randint(0, 40), r.uniform(60, 85))

    # Organic local posts — scaled to 850
    for _ in range(850):
        mk("o", lambda: r.choice(_RIOT_ORG), r.uniform(180, 3000), r.randint(60, 4000), r.uniform(-200, 200))

    posts.sort(key=lambda p: p.ts)
    return posts


# ─── Dataset D: journalist_doxxing ───────────────────────────────────────────

_DOX_BASE = dt.datetime(2026, 11, 18, 14, 0, tzinfo=dt.timezone.utc)
_TARGET_JOURNALIST = "mehak_writes"
_TARGET_ADDRESS    = "C-47 Sunrise Apartments, Koramangala"
_TARGET_PHONE      = "+91 9823401122"  # fictional

_DOX_HAR = [
    f"@{_TARGET_JOURNALIST} we know where you stay: {_TARGET_ADDRESS}. Stop writing about us or your family pays. #ExposeMehak",
    f"@{_TARGET_JOURNALIST} you will regret your last piece. Call her: {_TARGET_PHONE} tell her what you think. #ExposeMehak",
    f"Everyone mass-report @{_TARGET_JOURNALIST} and make her life hell. She deserves what is coming. #ExposeMehak",
    f"@{_TARGET_JOURNALIST} watch your back. We know your routine. Address shared: {_TARGET_ADDRESS} #ExposeMehak",
    f"RT to expose @{_TARGET_JOURNALIST} home address: {_TARGET_ADDRESS} phone {_TARGET_PHONE} #ExposeMehak",
]
_DOX_BRIGADE = [
    f"@{_TARGET_JOURNALIST} is a paid propaganda machine. Report this account #ReportMehak",
    f"Flag and report @{_TARGET_JOURNALIST} — spreading false narratives. #ReportMehak",
    f"Why is @{_TARGET_JOURNALIST} still on this platform? Mass report now! #ReportMehak",
    f"Boycott @{_TARGET_JOURNALIST} advertisers. Hit where it hurts. #BoycottMehak",
]
_DOX_ORG = [
    "Just finished a brilliant crime novel, highly recommend!", "Morning run done, feeling great #fitness",
    "Restaurant review: the new place on MG road is average at best", "Traffic in Koramangala is unbearable on Mondays",
    "Looking for a good dentist in Indiranagar any suggestions?", "Tech layoffs are scary, hope things stabilise soon",
    "Incredible street art near the underpass #art #bangalore", "Power cut for 3 hours today, lost all my work",
    "The winter chill is finally here in Bangalore!", "Local NGO doing great work, check them out #charity",
    "New metro station opened, saves 45 min commute", "Best filter coffee of my life this morning",
    "Startup ecosystem in Bangalore is buzzing #startups", "Hiring freeze at my company, worrying times #tech",
    "Road widening near Silk Board is causing chaos #traffic", "Loved the new Kannada film, go watch it #cinema",
    "Koramangala 5th block has the best street food scene", "Auto drivers need GPS training honestly",
    "Work from home productivity tips please, I am drowning", "Gym reopened after renovation, finally #fitness",
    "Book club meets this Saturday, all welcome #books", "Startup meetup at the co-working space Thursday evening",
    "Just adopted a kitten, life is complete #cats", "BBMP road repair — actually done well this time, shocker",
    "Namma Metro Phase 3 update anyone?", "Local vegetable vendor is more reliable than Zepto honestly",
    "Hackathon at the tech park this weekend #hackathon", "Blore weather is perfection in November, unpopular opinion",
    "Night cycling group starting at Cubbon Park, DM to join", "Indiranagar walking street Friday was so fun",
]
_CELEB_FANS = [
    "Love your work @zeenews_anchor! Keep it up!", "Great reporting @zeenews_anchor #journalism",
    "@zeenews_anchor brilliant piece today, shared with everyone", "Supporting good journalism @zeenews_anchor",
    "Brilliant investigative piece from @zeenews_anchor this week", "@zeenews_anchor deserves a national award #journalism",
    "Finally someone speaking truth to power @zeenews_anchor", "Sharing this everywhere @zeenews_anchor great work",
]


def generate_journalist_doxxing(seed: int = 13):
    """Dataset D — targeted harassment + doxxing of a journalist + brigading. 1000+ users."""
    r = random.Random(seed); posts = []; n = [0]
    base = _DOX_BASE

    def mk(kind, text_fn, age_days, followers, minute):
        n[0] += 1; uid = f"u{kind}{n[0]:04d}"
        created = base - dt.timedelta(days=age_days, hours=r.randint(0, 23))
        handle = f"{r.choice(['anon','burner','real','true','expose'])}_{r.choice(['user','id','acc','front','page'])}{r.randint(10,999)}"
        ts = base + dt.timedelta(minutes=minute, seconds=r.randint(0, 59))
        posts.append(Post(f"p{n[0]:05d}", uid, handle, created.isoformat(), ts.isoformat(),
                          text_fn(), followers, r.choice(["KA", "MH", "DL", "TN", "TS", "GJ"]), _phone(r)))

    # Campaign 1: doxxing + direct threats (55 accounts)
    for _ in range(55):
        mk("h", lambda: r.choice(_DOX_HAR), r.uniform(2, 18), r.randint(0, 50), r.uniform(0, 12))

    # Campaign 2: coordinated brigading / mass-report campaign (80 accounts)
    for _ in range(80):
        mk("b", lambda: r.choice(_DOX_BRIGADE), r.uniform(5, 30), r.randint(20, 200), r.uniform(40, 90))

    # Organic chatter — scaled to 820
    for _ in range(820):
        mk("o", lambda: r.choice(_DOX_ORG), r.uniform(180, 3000), r.randint(80, 5000), r.uniform(-240, 240))

    # Organic fan/support trap: friendly mentions of a different journalist (benign)
    for i in range(60):
        mk("f", lambda i=i: _CELEB_FANS[i % len(_CELEB_FANS)], r.uniform(300, 2500), r.randint(80, 4000), r.uniform(180, 210))

    posts.sort(key=lambda p: p.ts)
    return posts


# ─── Dataset E: cyberattack_infra ────────────────────────────────────────────

_CYBER_BASE = dt.datetime(2027, 6, 10, 9, 0, tzinfo=dt.timezone.utc)

_CYBER_RECRUIT = [
    "Paid job: need 5 people to run custom script on target IP {ip} port {port}. DM for wallet address. #TechJobs #RemoteWork",
    "Looking for technical help — stress-test tool for {ip}:{port}. ₹{pay}k for 2 hours work. Serious only. #FreelanceTech",
    "Urgent: Python devs needed. Run provided script on {ip} continuously. Anonymous only. Paid in crypto. #DevJobs",
    "Need people with good bandwidth to run load test on {ip}. Paying ₹{pay}k per session. DM asap. #TechGigs",
]
_CYBER_COORD = [
    "Tool ready. Start at 14:00 IST, target {ip}:{port}. Do not stop until I say. All go together. #Op{tag}",
    "Everyone ready for {ip}? Confirm here. 14:00 IST start. Low orbit ion cannon ready. #Op{tag}",
    "Sync up: {ip}:{port} is the target. All join at 14:00 IST sharp. Do not use home wifi. #Op{tag}",
    "Final check — is everyone on {ip}:{port}? Go at 14:00. Rotate VPNs every 10 min. #Op{tag}",
]
_CYBER_RUMOUR = [
    "EXCLUSIVE: {org} servers are wide open. Zero-day unpatched. Here is the link to the dump: {link} #Hacked #DataLeak",
    "Breaking: {org} database compromised. User data leaked. Download before it gets deleted: {link} #DataLeak",
    "Someone just posted {org} internal documents on paste. Link: {link} — forward before removed. #GovHack",
    "{org} has been hacked. Admin credentials in the paste: {link}. Share widely #DataLeak #CyberAttack",
]
_CYBER_ORG = [
    "Python 3.12 is blazing fast, finally upgraded", "Git merge conflicts are the real enemy #dev",
    "New AI model dropped, trying it out now #AI", "My home lab setup is getting out of hand #homelab",
    "Debugging for 3 hours, it was a missing semicolon #programminghumor", "Kubernetes cert prep is intense",
    "Open source contribution of the day done #opensource", "VSCode extension I wrote hit 1k downloads!",
    "Cloudflare outage analysis is fascinating reading #devops", "CTF challenge at 8pm tonight, join us #ctf",
    "Raspberry Pi 5 is amazing for home automation", "TypeScript is just better JS, fight me #typescript",
    "Container security talk at the local meetup was great #security", "My side project finally has users!",
    "Trying out Rust for the first time, the borrow checker is... something", "DevSecOps pipeline is finally green",
    "OWASP top 10 training done for the team #appsec", "Wireguard VPN setup guide I wrote got 10k views",
    "New CVE in a popular npm package, patch asap #security", "Bug bounty payout arrived, small win #bugbounty",
    "Stack Overflow is still the best for weird edge cases", "Hacktoberfest contributions submitted #opensource",
    "Cloud cost optimisation saved us ₹2L/month #aws", "Privacy by design should be default not optional",
    "Zero trust architecture webinar was informative #zerotrust", "Nmap scan of my own infra found an open port I forgot",
]


def generate_cyberattack_infra(seed: int = 55):
    """Dataset E — DDoS recruitment + data-leak rumours + coordination. 1010+ users."""
    r = random.Random(seed); posts = []; n = [0]
    base = _CYBER_BASE

    def mk(kind, text_fn, age_days, followers, minute):
        n[0] += 1; uid = f"u{kind}{n[0]:04d}"
        created = base - dt.timedelta(days=age_days, hours=r.randint(0, 23))
        handle = f"{r.choice(['anon','dark','null','void','cyber'])}{r.choice(['_ops','_sec','_lab','404','_hax'])}{r.randint(10,99)}"
        ts = base + dt.timedelta(minutes=minute, seconds=r.randint(0, 59))
        posts.append(Post(f"p{n[0]:05d}", uid, handle, created.isoformat(), ts.isoformat(),
                          text_fn(), followers, r.choice(["KA", "MH", "DL", "TN", "TS", "GJ", "HR", "UP"]), _phone(r)))

    targets = ["192.168.{}.{}".format(r.randint(1,254), r.randint(1,254)) for r in [random.Random(seed+i) for i in range(5)]]
    ports   = ["80", "443", "8080", "22", "3306"]
    orgs    = ["NationalPayments Corp", "StateElectricity Board", "CivicMunicipality Portal",
               "HealthMinistry Database", "RailwayTicketing API"]
    tags    = ["GhostOp", "SilentWave", "TidalForce", "ZeroDay"]
    links   = ["paste.site/abc123", "temp.link/xyz789", "darkpaste.net/op44"]
    pays    = ["5", "8", "12", "15"]

    # Campaign 1: DDoS recruitment (70 accounts)
    for _ in range(70):
        ip = r.choice(targets); port = r.choice(ports); pay = r.choice(pays)
        mk("r", lambda ip=ip, port=port, pay=pay: r.choice(_CYBER_RECRUIT).format(ip=ip, port=port, pay=pay),
           r.uniform(1, 10), r.randint(0, 80), r.uniform(0, 14))

    # Campaign 2: coordination / synchronised attack (55 accounts)
    for _ in range(55):
        ip = r.choice(targets); port = r.choice(ports); tag = r.choice(tags)
        mk("c", lambda ip=ip, port=port, tag=tag: r.choice(_CYBER_COORD).format(ip=ip, port=port, tag=tag),
           r.uniform(1, 6), r.randint(0, 40), r.uniform(40, 52))

    # Campaign 3: fake data-leak rumour to cause panic (40 accounts)
    for _ in range(40):
        org = r.choice(orgs); link = r.choice(links)
        mk("l", lambda org=org, link=link: r.choice(_CYBER_RUMOUR).format(org=org, link=link),
           r.uniform(2, 20), r.randint(0, 100), r.uniform(90, 130))

    # Organic tech community chatter — scaled to 845
    for _ in range(845):
        mk("o", lambda: r.choice(_CYBER_ORG), r.uniform(180, 3000), r.randint(50, 8000), r.uniform(-360, 360))

    posts.sort(key=lambda p: p.ts)
    return posts


# ─── Dataset F: stock_manipulation ───────────────────────────────────────────

_STOCK_BASE = dt.datetime(2027, 4, 7, 6, 30, tzinfo=dt.timezone.utc)   # market open day

_STOCK_PUMP = [
    "INSIDE TIP: {ticker} is going to explode today! Insiders buying heavily. Get in before 10am! #StockAlert #BuyNow",
    "My source in {co} says earnings are going to beat by 200%. {ticker} is a rocket. Limited time. #StockAlert",
    "Do not miss this: {ticker} technical breakout confirmed. Target ₹{tp}. Screenshot this. #StockTips #BuyNow",
    "URGENT: {ticker} halt expected after surprise announcement. Buy before markets figure it out! #StockAlert",
    "Operators are loading {ticker} heavily. Small cap, big move coming. This is not financial advice 😉 #StockAlert",
]
_STOCK_DUMP = [
    "Just sold all my {ticker} at ₹{sp}. Took my profits. Good luck everyone. #StockTips",
    "Smart money exiting {ticker} now. Sold at {sp}. This run is over. #StockTips #Portfolio",
    "Booked profits on {ticker} at ₹{sp}. On to the next one. Thanks for playing. #Trading",
]
_STOCK_FUD = [
    "WARNING: {ticker} promoters are quietly selling. Exit before retail gets trapped. #StockAlert #Scam",
    "BREAKING: SEBI probe into {ticker} insider trading. Exit immediately. #SEBIAlert #StockFraud",
    "Audit irregularities found in {co} books. {ticker} is a trap. Run. #StockFraud",
]
_STOCK_ORG = [
    "Quarterly results season is exciting #markets", "SIP discipline is the real wealth creator #investing",
    "Index funds are boring but they work #personalfinance", "My portfolio is down 3% today, not panicking",
    "Good article on Warren Buffett's annual letter this year", "NSE circuit breaker triggered again #Nifty",
    "Zerodha dashboard is clean, love the UX #fintech", "Mutual fund SIP date auto-deducted today",
    "SEBI new regulations on F&O are interesting #derivatives", "Gold is up again, hedge working #Gold",
    "RBI policy decision due Thursday, market is nervous #RBI", "Economy is recovering, consumption numbers good",
    "Small cap index outperforming large cap this quarter #stocks", "Checked my CIBIL score, all good #credit",
    "Dividend reinvestment is underrated #investing", "Tax loss harvesting done for the year #taxes",
    "UPI transaction crossed 10 billion a day milestone #fintech", "Groww app is intuitive for new investors",
    "Crypto regulation in India still unclear #crypto", "Real estate vs equity debate never ends #investment",
    "Nifty 50 PE ratio is elevated, being cautious #valuation", "Bond yields are creeping up #fixedincome",
    "Open interest data suggests big move coming in Bank Nifty", "Options expiry tomorrow, market will be volatile",
    "Angel One research report on pharma sector is good reading", "My ELSS lock-in period ends this month",
    "FII selling continues but DII absorbing it #markets", "Mid-cap rally has been impressive this year",
]


def generate_stock_manipulation(seed: int = 77):
    """Dataset F — pump-and-dump + FUD coordination on social media. 1020+ users."""
    r = random.Random(seed); posts = []; n = [0]
    base = _STOCK_BASE

    def mk(kind, text_fn, age_days, followers, minute):
        n[0] += 1; uid = f"u{kind}{n[0]:04d}"
        created = base - dt.timedelta(days=age_days, hours=r.randint(0, 23))
        handle = f"{r.choice(['trade','invest','fin','bull','market'])}{r.choice(['_guru','_alpha','_tips','_desk','_pro'])}{r.randint(10,99)}"
        ts = base + dt.timedelta(minutes=minute, seconds=r.randint(0, 59))
        posts.append(Post(f"p{n[0]:05d}", uid, handle, created.isoformat(), ts.isoformat(),
                          text_fn(), followers, r.choice(["MH", "GJ", "DL", "KA", "TN", "HR"]), _phone(r)))

    tickers = ["ZYMEX", "NOVABIO", "STARLINK500", "QUANTPHARMA", "HORITECH"]
    companies = ["Zymex Industries", "NovaBio Sciences", "Horizon Technologies",
                 "Quantum Pharma", "Star Link Ventures"]
    tps = ["180", "220", "340", "280", "450"]
    sps = ["175", "215", "330", "270", "440"]

    # Campaign 1: pump — coordinated buy-signal flooding (90 accounts)
    for _ in range(90):
        i = r.randint(0, len(tickers) - 1)
        ticker = tickers[i]; co = companies[i]; tp = tps[i]
        mk("p", lambda ticker=ticker, co=co, tp=tp: r.choice(_STOCK_PUMP).format(ticker=ticker, co=co, tp=tp),
           r.uniform(1, 12), r.randint(0, 200), r.uniform(0, 18))

    # Campaign 2: dump — coordinated sell-signal (45 accounts, 60-80 min later)
    for _ in range(45):
        i = r.randint(0, len(tickers) - 1)
        ticker = tickers[i]; sp = sps[i]
        mk("d", lambda ticker=ticker, sp=sp: r.choice(_STOCK_DUMP).format(ticker=ticker, sp=sp),
           r.uniform(5, 25), r.randint(100, 1000), r.uniform(60, 85))

    # Campaign 3: FUD after dump — push remaining holders to panic sell (40 accounts)
    for _ in range(40):
        i = r.randint(0, len(tickers) - 1)
        ticker = tickers[i]; co = companies[i]
        mk("f", lambda ticker=ticker, co=co: r.choice(_STOCK_FUD).format(ticker=ticker, co=co),
           r.uniform(5, 30), r.randint(0, 500), r.uniform(90, 130))

    # Organic finance community posts — scaled to 845
    for _ in range(845):
        mk("o", lambda: r.choice(_STOCK_ORG), r.uniform(180, 3000), r.randint(80, 15000), r.uniform(-240, 240))

    posts.sort(key=lambda p: p.ts)
    return posts


# ─── Dataset G: exam_paper_leak ──────────────────────────────────────────────

_EXAM_BASE = dt.datetime(2027, 5, 15, 2, 0, tzinfo=dt.timezone.utc)   # night before exam

_EXAM_LEAK = [
    "CONFIRMED: {exam} paper leaked. Questions attached below. Forward to all serious students. #ExamLeak #{tag}",
    "100% confirmed {exam} paper for tomorrow morning. DM ₹{fee} for PDF. Trusted source only. #ExamLeak #{tag}",
    "I have the {exam} paper. First 10 DMs get it free. Rest ₹{fee}. Act fast before it gets deleted! #ExamLeak",
    "BREAKING: {exam} paper sold in {city}. Police know but cannot act. Get it now while you can. #ExamLeak #{tag}",
    "Trusted source inside exam board leaked {exam} tomorrow questions. Join the group to get it. #ExamLeak",
]
_EXAM_SELL = [
    "Selling {exam} answer key. 95% accuracy guaranteed. Pay ₹{fee} to UPI and get PDF. Time limited. #StudyHelp",
    "Group buying {exam} paper for ₹{fee} per head. 20 people in already. DM to join. #StudyHelp #{tag}",
    "Exam tomorrow? I have {exam} full paper. ₹{fee} on GPay. Screenshot for proof. #ExamLeak",
    "Exam coaching group sharing {exam} leaked paper in Telegram. Link: t.me/examhelp{code} #StudyHelp",
]
_EXAM_WARN = [
    "Please do not fall for {exam} paper leak scams. They are all fake and you will be arrested. #AntiCheat",
    "UGC and {board} have confirmed no leak of {exam}. Anyone spreading this is lying. Report them. #AntiCheat",
    "Stay away from fake {exam} paper leak groups. You risk your career and your freedom. #AntiCheat",
]
_EXAM_ORG = [
    "Studying all night for tomorrow. Chai and focus. #exam", "Last minute revision is always stressful",
    "Hoping the paper is reasonable this year #competitive", "Our coaching centre mock test was harder than expected",
    "Syllabus for this exam is impossible wide, only 60% done", "All the best to everyone sitting tomorrow!",
    "Library was packed until midnight, good to see #students", "My notes from the entire semester in 4 pages",
    "Mobile signal at the exam centre is usually bad, download offline maps", "Slept 4 hours, exam in 3 hours",
    "Admit card printed and ready #prepared", "Centre is 2 hours away, leaving at 5am",
    "Practice paper from 2024 was very helpful #revision", "Teacher's predicted questions are usually right",
    "Nervous but prepared #competitive", "Exam hall instructions confuse me every time",
    "My coaching institute gives good short notes", "Post exam plan: sleep for 24 hours",
    "Board exams are more stressful for parents than students honestly", "Calculator allowed this time, relief",
    "Studying in group for the last 3 days straight", "Previous year papers are the best preparation",
    "Results take forever to come out #waiting", "Hope there are no surprise negative marking changes",
    "Subject teachers were excellent this year, grateful", "Parents are more anxious than I am honestly",
]


def generate_exam_paper_leak(seed: int = 33):
    """Dataset G — exam paper leak scam + answer key selling + organised cheating. 1015+ users."""
    r = random.Random(seed); posts = []; n = [0]
    base = _EXAM_BASE

    def mk(kind, text_fn, age_days, followers, minute):
        n[0] += 1; uid = f"u{kind}{n[0]:04d}"
        created = base - dt.timedelta(days=age_days, hours=r.randint(0, 23))
        handle = f"{r.choice(['study','result','exam','topper','coaching'])}{r.choice(['_buddy','_help','_guru','_zone','_tips'])}{r.randint(10,99)}"
        ts = base + dt.timedelta(minutes=minute, seconds=r.randint(0, 59))
        posts.append(Post(f"p{n[0]:05d}", uid, handle, created.isoformat(), ts.isoformat(),
                          text_fn(), followers, r.choice(["UP", "MP", "RJ", "BR", "DL", "JH", "UK", "HR"]), _phone(r)))

    exams  = ["JEE Main 2027", "UPSC Prelims", "SSC CGL", "NEET UG 2027", "GATE CS"]
    boards = ["NTA", "UPSC", "SSC Board", "NTA/NEET", "GATE Committee"]
    cities = ["Kota", "Patna", "Delhi", "Allahabad", "Jaipur", "Lucknow"]
    fees   = ["150", "200", "300", "500", "999"]
    tags   = ["JEE2027", "NEET2027", "UPSC2027", "SSC2027", "GATE2027"]
    codes  = ["jee27", "neet27", "upsc2027", "sscfree"]

    # Campaign 1: paper leak spread (75 accounts, very tight burst — night before exam)
    for _ in range(75):
        exam = r.choice(exams); fee = r.choice(fees); city = r.choice(cities)
        tag = r.choice(tags)
        mk("l", lambda exam=exam, fee=fee, city=city, tag=tag: r.choice(_EXAM_LEAK).format(exam=exam, fee=fee, city=city, tag=tag),
           r.uniform(1, 8), r.randint(0, 60), r.uniform(0, 12))

    # Campaign 2: answer-key selling (65 accounts)
    for _ in range(65):
        exam = r.choice(exams); fee = r.choice(fees); tag = r.choice(tags); code = r.choice(codes)
        mk("s", lambda exam=exam, fee=fee, tag=tag, code=code: r.choice(_EXAM_SELL).format(exam=exam, fee=fee, tag=tag, code=code),
           r.uniform(2, 20), r.randint(10, 500), r.uniform(50, 90))

    # Organic organic warning posts (10 accounts — benign anti-scam)
    for _ in range(10):
        exam = r.choice(exams); board = r.choice(boards)
        mk("w", lambda exam=exam, board=board: r.choice(_EXAM_WARN).format(exam=exam, board=board),
           r.uniform(100, 2000), r.randint(100, 5000), r.uniform(100, 200))

    # Organic exam chatter — scaled to 865
    for _ in range(865):
        mk("o", lambda: r.choice(_EXAM_ORG), r.uniform(60, 2000), r.randint(40, 4000), r.uniform(-480, 480))

    posts.sort(key=lambda p: p.ts)
    return posts


# ─── registry ────────────────────────────────────────────────────────────────

DATASETS = {
    "default":             (generate,                    7,  "Default — incitement + harassment + misinformation (mixed organic)"),
    "election_disinfo":    (generate_election_disinfo,  42,  "Election day — EVM-tampering claim + voter-suppression rumours"),
    "communal_riot":       (generate_communal_riot,     99,  "Communal unrest — imminent incitement + religious misinformation"),
    "journalist_doxxing":  (generate_journalist_doxxing, 13, "Journalist doxxing — threats + address/phone leak + brigading"),
    "cyberattack_infra":   (generate_cyberattack_infra, 55,  "Cyber infrastructure attack — DDoS recruitment + data-leak rumours"),
    "stock_manipulation":  (generate_stock_manipulation, 77, "Stock manipulation — coordinated pump-and-dump on social media"),
    "exam_paper_leak":     (generate_exam_paper_leak,   33,  "Exam paper leak scam — coordinated leak spread + answer-key selling"),
}


def load(name: str = "default", seed: int | None = None):
    """Return posts for a named dataset, optionally overriding the seed."""
    fn, default_seed, _ = DATASETS[name]
    return fn(seed if seed is not None else default_seed)


def list_datasets() -> list[dict]:
    return [{"name": k, "default_seed": v[1], "description": v[2]} for k, v in DATASETS.items()]
