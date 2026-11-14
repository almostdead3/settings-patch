#!/usr/bin/env python3
"""Patch Settings' OPMemberController so the top card falls back to the local
OnePlus account name when the OnePlus gateway call fails.

Usage: python3 patch_member.py <decoded Settings dir>
(the dir containing smali_classes2/com/oneplus/settings/OPMemberController.smali)
"""
import sys, pathlib

root = pathlib.Path(sys.argv[1])
f = root / "smali_classes2/com/oneplus/settings/OPMemberController.smali"
s = f.read_text()

if "applyLocalFallback" in s:
    sys.exit("already patched")

# 1) call the fallback in the 'server replied with an error' branch.
#    p0 is still 'this' right after :cond_7 (it is reused for the errCode string afterwards).
anchor = '    :cond_7\n    const-string p0, "errCode"'
assert s.count(anchor) == 1, "anchor for error branch not found exactly once"
s = s.replace(anchor,
    '    :cond_7\n'
    '    invoke-direct {p0}, Lcom/oneplus/settings/OPMemberController;->applyLocalFallback()V\n\n'
    '    const-string p0, "errCode"')

# 2) add the fallback method before useDynamicSliceSummary
method = r'''
.method private applyLocalFallback()V
    .locals 6

    :try_start_0
    iget-object v0, p0, Lcom/oneplus/settings/OPMemberController;->mContext:Landroid/content/Context;

    invoke-static {v0}, Landroid/accounts/AccountManager;->get(Landroid/content/Context;)Landroid/accounts/AccountManager;

    move-result-object v1

    const-string v2, "com.oneplus.account"

    invoke-virtual {v1, v2}, Landroid/accounts/AccountManager;->getAccountsByType(Ljava/lang/String;)[Landroid/accounts/Account;

    move-result-object v1

    array-length v2, v1

    if-nez v2, :cond_has

    # logged out: drop any stale cached name/avatar
    invoke-static {v0}, Landroidx/preference/PreferenceManager;->getDefaultSharedPreferences(Landroid/content/Context;)Landroid/content/SharedPreferences;

    move-result-object v0

    invoke-interface {v0}, Landroid/content/SharedPreferences;->edit()Landroid/content/SharedPreferences$Editor;

    move-result-object v0

    const-string v1, "member_title"

    invoke-interface {v0, v1}, Landroid/content/SharedPreferences$Editor;->remove(Ljava/lang/String;)Landroid/content/SharedPreferences$Editor;

    const-string v1, "member_avatar"

    invoke-interface {v0, v1}, Landroid/content/SharedPreferences$Editor;->remove(Ljava/lang/String;)Landroid/content/SharedPreferences$Editor;

    invoke-interface {v0}, Landroid/content/SharedPreferences$Editor;->apply()V

    goto :done

    :cond_has
    const/4 v2, 0x0

    aget-object v1, v1, v2

    iget-object v1, v1, Landroid/accounts/Account;->name:Ljava/lang/String;

    invoke-static {v1}, Landroid/text/TextUtils;->isEmpty(Ljava/lang/CharSequence;)Z

    move-result v2

    if-nez v2, :done

    iget-object v0, p0, Lcom/oneplus/settings/OPMemberController;->mOPMemberPreference:Lcom/oneplus/settings/ui/OPMemberPreference;

    if-eqz v0, :done

    new-instance v2, Ljava/util/HashMap;

    invoke-direct {v2}, Ljava/util/HashMap;-><init>()V

    const-string v3, "member_title"

    invoke-interface {v2, v3, v1}, Ljava/util/Map;->put(Ljava/lang/Object;Ljava/lang/Object;)Ljava/lang/Object;

    const-string v3, "member_content"

    const-string v4, "OnePlus Account"

    invoke-interface {v2, v3, v4}, Ljava/util/Map;->put(Ljava/lang/Object;Ljava/lang/Object;)Ljava/lang/Object;

    const-string v3, ""

    const-string v4, "member_avatar"

    invoke-interface {v2, v4, v3}, Ljava/util/Map;->put(Ljava/lang/Object;Ljava/lang/Object;)Ljava/lang/Object;

    const-string v4, "member_icon"

    invoke-interface {v2, v4, v3}, Ljava/util/Map;->put(Ljava/lang/Object;Ljava/lang/Object;)Ljava/lang/Object;

    const-string v4, "member_new_version"

    invoke-interface {v2, v4, v3}, Ljava/util/Map;->put(Ljava/lang/Object;Ljava/lang/Object;)Ljava/lang/Object;

    const-string v3, "token"

    const-string v4, "local"

    invoke-interface {v2, v3, v4}, Ljava/util/Map;->put(Ljava/lang/Object;Ljava/lang/Object;)Ljava/lang/Object;

    invoke-virtual {v0, v2}, Lcom/oneplus/settings/ui/OPMemberPreference;->setData(Ljava/util/Map;)V
    :try_end_0
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :catch_0

    :done
    return-void

    :catch_0
    move-exception v0

    invoke-virtual {v0}, Ljava/lang/Exception;->printStackTrace()V

    return-void
.end method
'''
m = ".method public bridge synthetic useDynamicSliceSummary()Z"
assert s.count(m) == 1
s = s.replace(m, method.lstrip("\n") + "\n" + m)
f.write_text(s)
print("patched", f)
