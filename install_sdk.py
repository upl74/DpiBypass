"""Non-interactive Android SDK + NDK install."""
import os, subprocess, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SDK = Path(os.environ.get("LOCALAPPDATA", "")) / "Android" / "Sdk"
STUDIO = Path(r"C:\Program Files\Android\Android Studio")
JAVA = STUDIO / "jbr"
SDKMANAGER = SDK / "cmdline-tools" / "latest" / "bin" / "sdkmanager.bat"

if not SDKMANAGER.exists():
    sys.exit(f"sdkmanager not found: {SDKMANAGER}")

env = os.environ.copy()
env["JAVA_HOME"] = str(JAVA)
env["ANDROID_SDK_ROOT"] = str(SDK)
env["ANDROID_HOME"] = str(SDK)

YES = ("y\n" * 200).encode()


def run(args, timeout=1800):
    print(">", " ".join(args))
    p = subprocess.Popen(
        args,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
        cwd=str(SDK),
    )
    out, _ = p.communicate(input=YES, timeout=timeout)
    text = out.decode(errors="replace")
    print(text[-3000:] if len(text) > 3000 else text)
    if p.returncode != 0:
        print(f"exit code {p.returncode}", file=sys.stderr)
    return p.returncode


run([str(SDKMANAGER), f"--sdk_root={SDK}", "--licenses"])

pkgs = [
    "platform-tools",
    "platforms;android-34",
    "build-tools;34.0.0",
    "ndk;27.2.12479018",
    "cmake;3.22.1",
]
rc = run([str(SDKMANAGER), f"--sdk_root={SDK}", "--install", *pkgs])
if rc != 0:
    sys.exit(rc)

props = SDK.parent.parent  # wrong
props_path = Path(__file__).parent / "local.properties"
props_path.write_text(f"sdk.dir={SDK.as_posix()}\n", encoding="ascii")
print("SDK installed:", SDK)
for name in ["platform-tools", "platforms", "build-tools", "ndk", "cmake"]:
    p = SDK / name
    print(name, "OK" if p.exists() else "MISSING")
