#!/usr/bin/env python3
"""Make Settings' member card use the India code path.

Why: OPMemberController picks the API by region.
  isIndia()  -> method "member.app.copywriting.get"   (same API family the Membership app uses; alive)
  otherwise  -> method "setting.copywriting.get"      (answers "api is circuit breaker" on the port)
isIndia() comes from OpCustomizeSettings.getSwType() == IN, a device property the port does not have.

This patch removes that SW-type check in the two places where it gates the card
(OPMemberController.isIndiaShow and OPMemberPreference.isIndia); the check that
com.oneplus.membership is installed stays.

Usage: python3 patch_india.py <decoded Settings dir>
"""
import sys, pathlib, re

root = pathlib.Path(sys.argv[1]) / "smali_classes2/com/oneplus/settings"
targets = [
    (root / "OPMemberController.smali",  "isIndiaShow"),
    (root / "ui/OPMemberPreference.smali", "isIndia"),
]
call = ("    invoke-static {}, Lcom/oneplus/settings/utils/OPUtils;->isIndia()Z\n\n"
        "    move-result v0\n")
for f, name in targets:
    s = f.read_text()
    m = re.search(r"\.method private %s\(\)Z.*?\.end method" % name, s, re.S)
    assert m, f"{name} not found in {f}"
    body = m.group(0)
    if "india-patched" in body:
        print("already patched:", f.name); continue
    assert body.count(call) == 1, f"unexpected body in {f.name}.{name}"
    new = body.replace(call, "    # india-patched: ignore SW type, keep the membership-app check\n    const/4 v0, 0x1\n")
    f.write_text(s.replace(body, new))
    print("patched", f.name, name)
