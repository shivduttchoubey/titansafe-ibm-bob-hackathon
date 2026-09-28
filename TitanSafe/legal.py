"""Indicative IPC -> BNS mapping. Decision support only; investigating officer + public prosecutor must confirm."""
M = {
 "incitement": [
  ("153A", "196", "Promoting enmity between groups on grounds of religion, race, place of birth, language etc."),
  ("505(2)", "353(2)", "Statements creating or promoting enmity, hatred or ill-will between classes"),
  ("107/109", "45/49", "Abetment (instigation) of an offence, if the act abetted is committed"),
  ("120B", "61(2)", "Criminal conspiracy (coordinated, pre-planned campaign)"),
  ("141/147", "189/191", "Unlawful assembly / rioting (if the call to gather materialises)")],
 "targeted_harassment": [
  ("506", "351", "Criminal intimidation"),
  ("354D", "78", "Stalking, including monitoring of online activity"),
  ("509", "79", "Word/gesture intended to insult the modesty of a woman (if victim is a woman)"),
  ("499/500", "356", "Defamation"),
  ("120B", "61(2)", "Criminal conspiracy (coordinated brigading)")],
 "organized_misinformation": [
  ("505(1)(b)", "353(1)(b)", "Statement likely to cause fear or alarm to the public"),
  ("153B", "197", "Imputations/assertions prejudicial to national integration (if targeting a community)"),
  ("505(2)", "353(2)", "Statements promoting enmity between classes (if communal framing)"),
  ("120B", "61(2)", "Criminal conspiracy (coordinated amplification)")]}
PROCESS = ["BNSS s.94 (CrPC s.91): notice for production of documents/records",
           "IT Act s.79(3)(b) + IT Rules 2021 r.3(1)(d): takedown notice to intermediary",
           "IT Act s.69A: blocking order via MeitY (only if content is severe and persistent)"]
def sections(threat, flags):
    rows = [dict(ipc=a, bns=b, title=t) for a, b, t in M[threat]]
    if flags.get("doxxing") and threat != "targeted_harassment":
        rows.append(dict(ipc="506", bns="351", title="Criminal intimidation (personal data leaked)"))
    return rows
