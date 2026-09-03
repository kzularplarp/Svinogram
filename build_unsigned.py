#!/usr/bin/env python3
"""
Build Telegram-iOS release-11.12 as an unsigned arm64 IPA for personal
sideload testing.

No third-party IPA is downloaded.
"""

from pathlib import Path
import glob
import json
import os
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
MAKE_DIR = ROOT / "build-system" / "Make"
sys.path.insert(0, str(MAKE_DIR))

from BazelLocation import locate_bazel  # type: ignore

def run(cmd, **kwargs):
    print("+", " ".join(str(x) for x in cmd), flush=True)
    subprocess.run([str(x) for x in cmd], check=True, **kwargs)

def make_configuration_repo(bazel_path: Path) -> Path:
    config_json = ROOT / "build-system" / "appstore-configuration.json"
    data = json.loads(config_json.read_text(encoding="utf-8"))

    repo = ROOT / "build-input" / "configuration-repository"
    provisioning = repo / "provisioning"
    provisioning.mkdir(parents=True, exist_ok=True)

    (repo / "WORKSPACE").write_text("", encoding="utf-8")
    (repo / "MODULE.bazel").write_text(
        'module(\n    name = "build_configuration",\n)\n',
        encoding="utf-8",
    )
    (repo / "BUILD").write_text("", encoding="utf-8")
    (provisioning / "BUILD").write_text("exports_files([])\n", encoding="utf-8")

    lines = [
        f'telegram_bazel_path = "{bazel_path}"',
        'telegram_use_xcode_managed_codesigning = False',
        f'telegram_bundle_id = "{data["bundle_id"]}"',
        f'telegram_api_id = "{data["api_id"]}"',
        f'telegram_api_hash = "{data["api_hash"]}"',
        f'telegram_team_id = "{data["team_id"]}"',
        f'telegram_app_center_id = "{data["app_center_id"]}"',
        f'telegram_is_internal_build = "{data["is_internal_build"]}"',
        f'telegram_is_appstore_build = "{data["is_appstore_build"]}"',
        f'telegram_appstore_id = "{data["appstore_id"]}"',
        f'telegram_app_specific_url_scheme = "{data["app_specific_url_scheme"]}"',
        f'telegram_premium_iap_product_id = "{data["premium_iap_product_id"]}"',
        'telegram_aps_environment = "development"',
        f'telegram_enable_siri = {bool(data["enable_siri"])}',
        f'telegram_enable_icloud = {bool(data["enable_icloud"])}',
        'telegram_enable_watch = True',
        '',
    ]
    (repo / "variables.bzl").write_text("\n".join(lines), encoding="utf-8")
    return repo

def main():
    os.chdir(ROOT)

    versions = json.loads((ROOT / "versions.json").read_text(encoding="utf-8"))
    if versions.get("app") != "11.12":
        raise SystemExit(f'Expected Telegram 11.12, got {versions.get("app")!r}')

    # Telegram's own helper downloads the exact Bazel binary declared in
    # versions.json and verifies its SHA-256.
    bazel = Path(locate_bazel(str(ROOT), None)).resolve()
    print("Bazel:", bazel)
    run([bazel, "--version"])

    config_repo = make_configuration_repo(bazel)

    cache_dir = Path.home() / "telegram-bazel-cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    jobs = str(max(2, os.cpu_count() or 4))
    build_number = "12001"

    cmd = [
        bazel,
        "build",
        "Telegram/Telegram",
        f"--override_repository=build_configuration={config_repo}",
        "--announce_rc",
        "--features=swift.use_global_module_cache",
        "--verbose_failures",
        "--features=swift.skip_function_bodies_for_derived_files",
        f"--jobs={jobs}",
        f"--define=buildNumber={build_number}",
        "--define=telegramVersion=11.12",
        f"--disk_cache={cache_dir}",
        "-c", "opt",
        "--ios_multi_cpus=arm64",
        "--watchos_cpus=arm64_32",
        "--features=swift.opt_uses_wmo",
        "--features=swift.opt_uses_osize",
        "--features=dead_strip",
        "--objc_enable_binary_stripping",
        "--//Telegram:disableProvisioningProfiles",
        "--//Telegram:disableExtensions",
    ]

    run(cmd)

    candidates = []
    for pattern in (
        "bazel-bin/Telegram/Telegram.ipa",
        "bazel-out/**/bin/Telegram/Telegram.ipa",
    ):
        candidates.extend(glob.glob(pattern, recursive=True))

    seen = set()
    unique = []
    for p in candidates:
        if p not in seen:
            seen.add(p)
            unique.append(p)
    candidates = unique

    if not candidates:
        raise SystemExit("Build succeeded but Telegram.ipa could not be found.")

    ipa = Path(candidates[0]).resolve()
    print("Found IPA:", ipa)

    out_dir = ROOT / "out"
    out_dir.mkdir(exist_ok=True)
    dst = out_dir / "Telegram-11.12-unsigned.ipa"
    shutil.copy2(ipa, dst)

    run(["unzip", "-tq", dst])

    print("\nDONE:", dst)
    run(["shasum", "-a", "256", dst])

if __name__ == "__main__":
    main()
