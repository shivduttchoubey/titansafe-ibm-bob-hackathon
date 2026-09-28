import json, copy
from TitanSafe import mock, detect, brief, dashboard
from TitanSafe.workflow import Case
from TitanSafe.audit import verify_chain
from TitanSafe.abstraction import verify_attestation, verify_t1, verify_t2, Vault
from TitanSafe.cli import run_demo, run_verify

def setup():
    ps = mock.generate(7); return ps, detect.detect(ps)

def test_detects_three_campaigns_and_no_organic_false_positives():
    ps, cl = setup()
    assert sorted(c["threat_type"] for c in cl) == ["incitement", "organized_misinformation", "targeted_harassment"]
    assert all(not p.user_id.startswith(("uo", "uk", "uf")) for c in cl for i in c["post_idx"] for p in [ps[i]])

def test_no_pii_in_lea_view_or_brief():
    ps, cl = setup(); case = Case("C1", ps, cl)
    case.request(1, "LEA", ["N"], clusters=["CL-01", "CL-02", "CL-03"], purpose="x", legal_basis="y")
    view = case.lea_view(); b, md = brief.build(view); blob = json.dumps(view) + md + dashboard.render(view, b)
    for p in ps:
        assert p.user_id not in blob and p.handle not in blob and p.phone_on_file not in blob
    assert "9876501234" not in blob and "[PHONE]" in blob     # doxxed number redacted but flagged

def test_policy_gates():
    ps, cl = setup(); c = Case("C2", ps, cl)
    assert c.request(1, "L", clusters=["CL-01"], purpose="p")["status"] == "DENIED"
    assert c.request(1, "L", ["N"], clusters=["CL-01"], purpose="p", legal_basis="b")["status"] == "DISCLOSED"
    ps1 = [a["pseudonym"] for a in c.t1[0]["accounts"][:2]]
    assert c.request(2, "L", ["N"], pseudonyms=ps1, purpose="p", legal_basis="b", order_ref="O")["status"] == "DENIED"  # single approver
    assert c.request(2, "L", ["N", "M"], pseudonyms=["PSN-nope"], purpose="p", legal_basis="b", order_ref="O")["status"] == "DENIED"
    assert c.request(2, "L", ["N", "M"], pseudonyms=ps1, purpose="p", legal_basis="b", order_ref="O")["status"] == "DISCLOSED"
    assert verify_chain(c.audit.entries) and len(c.t2) == 2

def test_crypto_verifies_and_tampering_fails():
    ps, cl = setup(); c = Case("C3", ps, cl)
    c.request(1, "L", ["N"], clusters=["CL-01"], purpose="p", legal_basis="b")
    c.request(2, "L", ["N", "M"], pseudonyms=[c.t1[0]["accounts"][0]["pseudonym"]], purpose="p", legal_basis="b", order_ref="O")
    assert all(x[2] for x in verify_attestation(c.att)) and verify_t1(c.att, c.t1)[1] == 0 and verify_t2(c.t1, c.t2)[1] == 0
    t1 = copy.deepcopy(c.t1); t1[0]["posts"][0]["post_id"] = "p99999"; assert verify_t1(c.att, t1)[1] == 1     # swapped evidence
    t2 = copy.deepcopy(c.t2); t2[0]["user_id"] = "someone-else"; assert verify_t2(c.t1, t2)[1] == 1            # wrong identity
    att = copy.deepcopy(c.att); att["clusters"][0]["zk_min_accounts"][0]["k"] = 99
    assert not all(x[2] for x in verify_attestation(att))                                                       # forged claim
    e = copy.deepcopy(c.audit.entries); e[1]["detail"]["tier"] = 0; assert not verify_chain(e)

def test_pseudonyms_unlinkable_across_cases():
    ps, cl = setup(); u = ps[cl[0]["post_idx"][0]].user_id
    assert Vault("A", ps, cl).pseudo(u) != Vault("B", ps, cl).pseudo(u)

def test_demo_end_to_end(tmp_path):
    run_demo(str(tmp_path), quiet=True); assert run_verify(str(tmp_path))
