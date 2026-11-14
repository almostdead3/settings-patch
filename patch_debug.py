#!/usr/bin/env python3
"""Debug patch for Settings' OPMemberController.

 - logs the deviceId that is sent to the OnePlus gateway          (tag OPMemberController, "req deviceId=")
 - logs whether token / heyTapToken are empty ("req token empty=", "req heyTapToken empty=")
 - logs the full reply of the member request                     (tag OPMemberController, "resp=")
 - with --spoof-deviceid: if the SafeProvider UUID is empty, sends the
   phone's ANDROID_ID instead (experiment: does the server accept a non-empty id?)

Usage: python3 patch_debug.py <decoded Settings dir> [--spoof-deviceid]
"""
import sys, pathlib

root = pathlib.Path(sys.argv[1])
spoof = "--spoof-deviceid" in sys.argv
f = root / "smali_classes2/com/oneplus/settings/OPMemberController.smali"
s = f.read_text()
if "req deviceId=" in s:
    sys.exit("already patched")

def once(old, new):
    global s
    assert s.count(old) == 1, "anchor not found exactly once:\n" + old
    s = s.replace(old, new)

# more registers in getData() and success()
once(".method private getData(Ljava/lang/String;)V\n    .locals 7",
     ".method private getData(Ljava/lang/String;)V\n    .locals 9")
once(".method public success(Lokhttp3/Call;Lokhttp3/Response;)V\n    .locals 7",
     ".method public success(Lokhttp3/Call;Lokhttp3/Response;)V\n    .locals 9")

# --- deviceId: optional fallback + log ---
old = ('    invoke-static {v6}, Lcom/oneplus/settings/utils/OPUtils;->getOPSafeUUID(Landroid/content/Context;)Ljava/lang/String;\n\n'
       '    move-result-object v6\n')
assert s.count(old) == 1
fallback = ''
if spoof:
    fallback = '''
    invoke-static {v6}, Landroid/text/TextUtils;->isEmpty(Ljava/lang/CharSequence;)Z

    move-result v7

    if-eqz v7, :dbg_keep_id

    iget-object v7, p0, Lcom/oneplus/settings/OPMemberController;->mContext:Landroid/content/Context;

    invoke-virtual {v7}, Landroid/content/Context;->getContentResolver()Landroid/content/ContentResolver;

    move-result-object v7

    const-string v8, "android_id"

    invoke-static {v7, v8}, Landroid/provider/Settings$Secure;->getString(Landroid/content/ContentResolver;Ljava/lang/String;)Ljava/lang/String;

    move-result-object v6

    :dbg_keep_id
'''
log = '''
    new-instance v7, Ljava/lang/StringBuilder;

    invoke-direct {v7}, Ljava/lang/StringBuilder;-><init>()V

    const-string v8, "req deviceId="

    invoke-virtual {v7, v8}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v7, v6}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v7}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v7

    const-string v8, "OPMemberController"

    invoke-static {v8, v7}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I
'''
s = s.replace(old, old + fallback + log)


# --- log whether the account tokens that Settings sends are empty (never the values) ---
def tok_log(label, reg):
    return f"""
    invoke-static {{{reg}}}, Landroid/text/TextUtils;->isEmpty(Ljava/lang/CharSequence;)Z

    move-result v7

    new-instance v8, Ljava/lang/StringBuilder;

    invoke-direct {{v8}}, Ljava/lang/StringBuilder;-><init>()V

    const-string v5, "{label}"

    invoke-virtual {{v8, v5}}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {{v8, v7}}, Ljava/lang/StringBuilder;->append(Z)Ljava/lang/StringBuilder;

    invoke-virtual {{v8}}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v8

    const-string v5, "OPMemberController"

    invoke-static {{v5, v8}}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I
"""
a = ('    .line 230\n'
     '    invoke-virtual {p1, v5, v2}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;\n')
once(a, a + tok_log("req token empty=", "v2"))
b = '    .line 233\n    :cond_3\n'
once(b, b + tok_log("req heyTapToken empty=", "v3"))

# --- log the reply of the member request ---
old = ('    invoke-virtual {v4}, Lokhttp3/ResponseBody;->string()Ljava/lang/String;\n\n'
       '    move-result-object v4\n')
assert s.count(old) == 1, s.count(old)
# the member reply is the one inside success() of the main class, after the "title" const; patch the first
# occurrence that is inside success(Lokhttp3/Call;Lokhttp3/Response;)V
i = s.index(".method public success(Lokhttp3/Call;Lokhttp3/Response;)V")
j = s.index(old, i)
resp_log = '''
    const-string v7, "OPMemberController"

    new-instance v8, Ljava/lang/StringBuilder;

    invoke-direct {v8}, Ljava/lang/StringBuilder;-><init>()V

    const-string v6, "resp="

    invoke-virtual {v8, v6}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v8, v4}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v8}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v8

    invoke-static {v7, v8}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I
'''
s = s[:j + len(old)] + resp_log + s[j + len(old):]
f.write_text(s)
print("patched", f, "(spoof deviceId)" if spoof else "")
