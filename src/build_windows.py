"""Build separate native Windows executables using upstream's dependency rules.

No source generation, scientific rewrites, or global linker overrides. Objects
live in src/.windows so Linux/macOS builds cannot reuse Windows objects.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

SRC = Path(__file__).resolve().parent
ROOT = SRC.parent
OBJECTS = SRC / ".windows"
BIN = ROOT / "bin"
NICK = "strsubs sortit vsubs statsubs linsubs getpars xsearch gauss gds".split()
EXTRA = "rolloff rolloffp ascore diffmean gcount kimf mkweights qpdslow qpfit qpfmvmix".split()
BLOCKED = {"qpfmvmix": "upstream contains undeclared q/ab and an incomplete pops[ab expression; no buildable Linux reference"}


def inventory():
    makefile = (SRC / "Makefile").read_text()
    defaults = set()
    for group in ("PROGS", "PROGS3", "PROGS4"):
        defaults.update(re.search(rf"^{group}\s*=\s*(.+)$", makefile, re.M)[1].split())
    programs = sorted(defaults | set(EXTRA))
    rules = {}
    for program in programs:
        match = re.search(rf"^{re.escape(program)}:\s*([^\n]*)", makefile, re.M)
        if not match:
            raise RuntimeError(f"No upstream link rule for {program}")
        # Upstream's qpfmvmix rule has a typo, eigx.. instead of eigx.o.
        tokens = match[1].replace("eigx..", "eigx.o").split()
        sources = [token[:-2] + ".c" for token in tokens if token.endswith(".o")]
        for source in sources:
            if not (SRC / source).is_file():
                raise RuntimeError(f"Missing source for {program}: {source}")
        rules[program] = sources
    return defaults, rules


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--toolchain", type=Path)
    parser.add_argument("--tools", nargs="+")
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args()
    defaults, rules = inventory()
    if args.list:
        for program in rules:
            print(f"{program}: {('BLOCKED: ' + BLOCKED[program]) if program in BLOCKED else ('upstream default' if program in defaults else 'additional upstream target')}")
        print(f"{len(rules) - len(BLOCKED)} build targets ({len(defaults)} upstream defaults); {len(BLOCKED)} blocked upstream target")
        return
    if os.name != "nt" or not args.toolchain:
        parser.error("Use build-windows.ps1 on Windows with an MSYS2 UCRT64 toolchain")
    selected = args.tools or [p for p in rules if p not in BLOCKED]
    unknown = set(selected) - rules.keys()
    if unknown:
        parser.error(f"Unknown tools: {', '.join(sorted(unknown))}")
    for program in selected:
        if program in BLOCKED:
            parser.error(f"{program}: {BLOCKED[program]}")
    compiler = args.toolchain.resolve() / "gcc.exe"
    archiver = args.toolchain.resolve() / "ar.exe"
    objdump = args.toolchain.resolve() / "objdump.exe"
    windres = args.toolchain.resolve() / "windres.exe"
    OBJECTS.mkdir(exist_ok=True)
    BIN.mkdir(exist_ok=True)
    argp = OBJECTS / "argp"
    if any(p in selected for p in ("transpose", "merge_transpose")) and not (argp / "lib/libargp.a").is_file():
        parser.error("GNU argp is missing: run prepare-windows.ps1 first")
    flags = ["-std=gnu11", "-fno-common", "-ffp-contract=off", "-fno-fast-math",
             "-D__USE_MINGW_ANSI_STDIO=1", "-D_FILE_OFFSET_BITS=64",
             "-I.", "-Inicksrc", f"-I{argp / 'include'}", "-include", "win32/compat.h"]
    # Match the 8 MiB main-thread allowance of the pinned Linux reference.
    # MinGW's default 2 MiB reserve can fail earlier on recursive/stack-heavy
    # inputs. This reserves address space; it does not precommit 8 MiB of RAM.
    link_flags = ["-Wl,--stack,8388608"]
    compiler_version = subprocess.check_output([str(compiler), "--version"], text=True).splitlines()[0]
    headers = sorted(SRC.glob("*.h")) + sorted((SRC / "nicksrc").glob("*.h")) + sorted((SRC / "win32").glob("*.h"))
    signature = hashlib.sha256((compiler_version + str(compiler) + repr(flags)).encode())
    for header in headers:
        signature.update(header.read_bytes())
    if (argp / "include/argp.h").is_file():
        signature.update((argp / "include/argp.h").read_bytes())

    def run(command):
        subprocess.run([str(x) for x in command], cwd=SRC, check=True)

    def obj(source):
        return OBJECTS / (source.replace("/", "_").removesuffix(".c") + ".o")

    sources = set(source for program in selected for source in rules[program])
    sources.update(f"nicksrc/{name}.c" for name in NICK)
    sources.add("win32/compat.c")
    # Content-based dependencies include shared headers, flags and compiler.
    for source in sorted(sources):
        optimization = "-O3" if source.startswith("nicksrc/") else "-O2"
        digest = hashlib.sha256(signature.digest() + (SRC / source).read_bytes() + optimization.encode()).hexdigest()
        stamp = obj(source).with_suffix(".sha256")
        if obj(source).is_file() and stamp.is_file() and stamp.read_text() == digest:
            continue
        print(f"Compiling {source}", flush=True)
        run([compiler, *flags, optimization, "-c", source, "-o", obj(source)])
        stamp.write_text(digest)
    nick = OBJECTS / "libnick.a"
    # Recreate the archive so deleted upstream members cannot survive a rebuild.
    if nick.exists():
        nick.unlink()
    run([archiver, "rcs", nick, *(obj(f"nicksrc/{name}.c") for name in NICK)])
    # UTF-8 paths/argv without changing the machine's code page. The manifest
    # also opts into Windows' configured long-path support (Windows 10 1903+).
    manifest = SRC / 'win32/admixtools.manifest'
    resource = OBJECTS / 'admixtools-resource.o'
    run([windres, '-I', SRC / 'win32', '-i', SRC / 'win32/admixtools.rc', '-o', resource])
    for program in selected:
        print(f"Linking {program}.exe", flush=True)
        libraries = ["-lgsl", "-lopenblas", "-lz", "-lm"]
        if program in ("transpose", "merge_transpose"):
            libraries.extend([f"-L{argp / 'lib'}", "-largp"])
        run([compiler, *link_flags, *(obj(s) for s in rules[program]), obj("win32/compat.c"),
             nick, resource, *libraries, "-o", BIN / f"{program}.exe"])
    # Copy the dependency closure, including Fortran/OpenMP runtime DLLs. Refuse
    # missing non-system DLLs instead of producing binaries that will not launch.
    pending = [BIN / f"{program}.exe" for program in selected]
    copied = set()
    while pending:
        binary = pending.pop()
        output = subprocess.check_output([str(objdump), "-p", str(binary)], text=True)
        for name in re.findall(r"DLL Name:\s*(\S+)", output):
            dependency = args.toolchain / name
            if name.lower() in copied:
                continue
            if dependency.is_file():
                shutil.copy2(dependency, BIN / name)
                copied.add(name.lower())
                pending.append(BIN / name)
            elif not (Path(os.environ["SystemRoot"]) / "System32" / name).is_file() and not name.lower().startswith(("api-ms-", "ext-ms-")):
                raise RuntimeError(f"Missing dependency {name} for {binary.name}")
    # Keep the helpers in their upstream installed locations. They still require
    # their respective interpreters; they are not converted to .exe programs.
    for filename in ("rexpfit.r", "wtjack.pl", "fxtract"):
        shutil.copy2(SRC / filename, BIN / filename)
    for helper in (ROOT / "perlsrc").iterdir():
        if helper.is_file():
            shutil.copy2(helper, BIN / helper.name)
    shutil.copytree(SRC / "script", BIN / "script", dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    license_root = args.toolchain.parent / "share/licenses"
    for package in ("gsl", "openblas", "zlib", "libgcc", "libgfortran", "libgomp", "libquadmath", "libwinpthread"):
        if (license_root / package).is_dir():
            shutil.copytree(license_root / package, BIN / "licenses" / package, dirs_exist_ok=True)
    argp_source = OBJECTS / "argp-source"
    for notice in [*argp_source.glob("COPYING*"), argp_source / "README.md", argp_source / "argp.h"]:
        if notice.is_file():
            (BIN / "licenses/argp").mkdir(parents=True, exist_ok=True)
            shutil.copy2(notice, BIN / "licenses/argp" / notice.name)
    metadata = {
        "upstream_commit": (ROOT / "UPSTREAM_BASELINE").read_text().strip(),
        "working_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "compiler": compiler_version,
        "zlib_header_version": re.search(r'^#define ZLIB_VERSION "([^"]+)"',
            (args.toolchain.parent / "include/zlib.h").read_text(), re.M)[1],
        "flags": flags, "link_flags": link_flags,
        "optimization": {"nicksrc": "-O3", "other": "-O2"},
        "executables": selected, "runtime_dlls": sorted(copied),
        "runtime_sha256": {name: hashlib.sha256((BIN / name).read_bytes()).hexdigest() for name in sorted(copied)},
        "source_sha256": {source: hashlib.sha256((SRC / source).read_bytes()).hexdigest() for source in sorted(sources)},
        "header_signature": signature.hexdigest(),
        "manifest_sha256": hashlib.sha256(manifest.read_bytes()).hexdigest(),
        "script_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in sorted((SRC / "script").glob("*.py"))},
        "parity_validated": False,
    }
    (BIN / "windows-build.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(f"Built {len(selected)} executables in {BIN}. Numerical parity requires separate validation.")


if __name__ == "__main__":
    main()
