#!/usr/bin/env python3
"""Make OnePlus' Google-tile card-layout check also match the new
Play services key (top_level_google). Keeps the old class-based match."""
import sys

path = sys.argv[1] if len(sys.argv) > 1 else \
    "Settings_src/smali/com/android/settings/dashboard/DashboardFragment.smali"
s = open(path, encoding="utf-8").read()

old = '''    const-string v7, "com.google.android.gms.app.settings"

    invoke-virtual {v6, v7}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z

    move-result v6

    if-eqz v6, :cond_7
'''

new = '''    const-string v7, "com.google.android.gms.app.settings"

    invoke-virtual {v6, v7}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z

    move-result v7

    if-nez v7, :cond_gms_card

    const-string v7, "top_level_google"

    invoke-virtual {v6, v7}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z

    move-result v6

    if-eqz v6, :cond_7

    :cond_gms_card
'''

if "cond_gms_card" in s:
    sys.exit("already patched")
if s.count(old) != 1:
    sys.exit("pattern not found exactly once (found %d); not patched" % s.count(old))
open(path, "w", encoding="utf-8").write(s.replace(old, new))
print("patched", path)
