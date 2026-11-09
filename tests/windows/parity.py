"""Deterministic Linux/Windows integration cases with strict output comparison.

Run on each OS with --bin and --output; compare the two output directories with
--compare. Raw streams, data files, return codes, and a diff are retained.
"""
import argparse
import difflib
import hashlib
import json
import os
from pathlib import Path
import random
import re
import shutil
import subprocess
import sys


def fixtures(work):
    work.mkdir(parents=True, exist_ok=True)

    def write(name, text):
        (work / name).write_text(text, encoding="ascii", newline="\n")

    rng = random.Random(1907)
    populations = "Out A B C X R1 R2 R3 R4".split()
    write("input.ind", "".join(f"{p}{i} U {p}\n" for p in populations for i in range(6)))
    snps, genotypes = [], []
    for index in range(2200):
        chrom, position = index // 100 + 1, index % 100 + 1
        snps.append(f"rs{index:05d} {chrom} {position * .001:.6f} {position * 10000} A G\n")
        base = rng.uniform(.2, .8)
        frequencies = [min(.95, max(.05, base + rng.uniform(-.18, .18))) for _ in populations]
        frequencies[4] = .6 * frequencies[1] + .4 * frequencies[2]
        genotypes.append("".join(str(int(rng.random() < f) + int(rng.random() < f)) for f in frequencies for _ in range(6)) + "\n")
    write("input.snp", "".join(snps))
    write("input.geno", "".join(genotypes))
    write("small.snp", "".join(snps[:40]))
    write("small.geno", "".join(genotypes[:40]))
    write("pops", "\n".join(populations) + "\n")
    write("left", "X\nA\nB\n")
    write("right", "Out\nR1\nR2\nR3\nR4\n")
    write("triples", "A B X\nA C X\n")
    write("quads", "Out A B X\nOut C A X\n")
    write("ratios", "Out A X B Out A C B\n")
    write("diffs", "Out A B X Out C A X\n")
    write("refs", "A\nB\n")
    write("jack", "0 40 .2\n1 10 .19\n2 10 .21\n3 10 .18\n4 10 .22\n")
    write("weights", "1 10 .19\n2 10 .21\n3 10 .18\n4 10 .22\n")
    write("mean1", "100 200\n400 0\n0 900\n")
    write("mean2", "120 180\n400 0\n0 900\n")
    write("graph", "root R\nlabel Out O\nlabel A A\nlabel B B\nlabel C C\nlabel X X\nedge o R O\nedge q R Q\nedge ab Q AB\nedge a AB A\nedge b AB B\nedge c Q C\nadmix XX AB C 60 40\nedge x XX X\n")
    base = "genotypename: input.geno\nsnpname: input.snp\nindivname: input.ind\nseed: 77\nblgsize: .005\n"
    parameters = {
        "qp3Pop": "popfilename: triples\n",
        "qpDstat": "popfilename: quads\n",
        "qpDstat-f4": "popfilename: quads\nf4mode: YES\n",
        "qpDstat-random": "popfilename: quads\npopsizelimit: 3\n",
        "qpF4ratio": "popfilename: ratios\n",
        "qp4diff": "popfilename: diffs\n",
        "qpAdm": "popleft: left\npopright: right\n",
        "qpAdm-allsnps": "popleft: left\npopright: right\nallsnps: YES\n",
        "qpWave": "popleft: left\npopright: right\n",
        "qpWave-allsnps": "popleft: left\npopright: right\nallsnps: YES\n",
        "qpfstats": "poplistname: pops\nfstatsoutname: output.fstats\nhires: YES\n",
        "qpfmv": "fstatsname: output.fstats\npopfilename: quads\nfmvoutname: output.fmv\n",
        "qpff3base": "poplistname: pops\n",
        "easystats": "poplistname: pops\n",
        "easycheck": "poplistname: pops\n",
        "easylite": "poplistname: pops\n",
        "convertf": "outputformat: PACKEDANCESTRYMAP\ngenotypeoutname: output.geno\nsnpoutname: output.snp\nindivoutname: output.ind\n",
        "rolloff": "poplistname: refs\nadmixpop: X\noutput: rolloff.out\nmaxdis: .02\nbinsize: .001\ncheckmap: YES\n",
        "rolloffp": "poplistname: refs\nadmixpop: X\noutput: rolloffp.out\nmaxdis: .02\nbinsize: .001\ncheckmap: YES\n",
        "qpGraph": "outpop: Out\nlsqmode: YES\ndiag: .0001\nhires: YES\n",
    }
    for name, extra in parameters.items():
        selected_base = base.replace("input.snp", "small.snp").replace("input.geno", "small.geno") if name in ("easystats", "easylite", "easycheck") else base
        write(f"par.{name}", selected_base + extra)
    # Distinct individual IDs for an actual genotype merge.
    write("other.ind", "".join(f"Z{p}{i} U {p}\n" for p in populations for i in range(6)))
    write("par.mergeit", "geno1: input.geno\nsnp1: input.snp\nind1: input.ind\ngeno2: input.geno\nsnp2: input.snp\nind2: other.ind\noutputformat: PACKEDANCESTRYMAP\noutstem: merged\n")
    # Includes 0x0a, 0x0d, 0x1a and 0xff: CRT text mode would corrupt this.
    header = ("TGENO %7d %7d %x %x" % (5, 64, 0, 0)).encode().ljust(48, b"\0")
    (work / "binary.tgeno").write_bytes(header + bytes(range(79)) + b"\xff")
    write("transpose.list", "binary.tgeno\nbinary.tgeno\n")


def cases():
    result = []
    for name in ("qpfstats", "qp3Pop", "qpDstat", "qpDstat-f4", "qpDstat-random", "qpF4ratio", "qp4diff",
                 "qpAdm", "qpAdm-allsnps", "qpWave", "qpWave-allsnps", "qpfmv", "qpff3base",
                 "easystats", "easycheck", "easylite", "convertf", "mergeit", "rolloff", "rolloffp"):
        result.append((name, name.split("-")[0], ["-p", f"par.{name}"]))
    result += [
        ("qpGraph", "qpGraph", ["-p", "par.qpGraph", "-g", "graph", "-o", "graph.out"]),
        ("qpreroot", "qpreroot", ["-g", "graph", "-o", "reroot.out"]),
        ("nickhash", "nickhash", ["-i", "input.ind"]),
        ("grabpars", "grabpars", ["-p", "par.qpAdm", "-x", "seed:"]),
        ("simpjack2", "simpjack2", ["-i", "jack"]),
        ("dowtjack", "dowtjack", ["-i", "weights", "-o", "weighted.out", "-m", ".2"]),
        ("diffmean", "diffmean", ["-i", "mean1", "-j", "mean2", "-x"]),
        ("transpose", "transpose", ["binary.tgeno", "transposed.geno"]),
        ("transpose-lowmem", "transpose", ["-m", "binary.tgeno", "transposed-lowmem.geno"]),
        ("transpose-roundtrip", "transpose", ["transposed.geno", "roundtrip.tgeno"]),
        ("geno_single", "geno_single", ["binary.tgeno", "2", "single.tgeno"]),
        ("merge_transpose", "merge_transpose", ["-l", "transpose.list", "-o", "merged.tgeno"]),
        ("transpose-help", "transpose", ["--help"]),
        ("merge_transpose-help", "merge_transpose", ["--help"]),
        ("transpose-invalid", "transpose", ["--no-such-option"]),
    ]
    return result


def run(binary_dir, output):
    output.mkdir(parents=True, exist_ok=True)
    work = output / "working directory with spaces"
    fixtures(work)
    env = dict(os.environ, OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1", OPENBLAS_CORETYPE="NEHALEM", LC_ALL="C", STMP="tmp")
    (work / "tmp").mkdir(exist_ok=True)
    env["PATH"] = str(binary_dir) + os.pathsep + env.get("PATH", "")
    manifest = {"binary_dir": str(binary_dir), "platform": sys.platform, "cases": {}, "environment": {k: env[k] for k in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "OPENBLAS_CORETYPE", "LC_ALL", "STMP")}}
    for name, tool, arguments in cases():
        executable = binary_dir / (tool + (".exe" if os.name == "nt" else ""))
        if not executable.is_file():
            manifest["cases"][name] = {"missing": True}
            print(f"MISSING {name}", flush=True)
            continue
        try:
            command = [executable.name, *arguments]
            completed = subprocess.run(command, executable=str(executable), cwd=work, env=env, capture_output=True, timeout=90)
            (output / f"{name}.stdout").write_bytes(completed.stdout)
            (output / f"{name}.stderr").write_bytes(completed.stderr)
            manifest["cases"][name] = {"returncode": completed.returncode, "arguments": arguments}
            print(f"{name}: {completed.returncode}", flush=True)
        except subprocess.TimeoutExpired:
            manifest["cases"][name] = {"timeout": True}
            print(f"TIMEOUT {name}", flush=True)
    for filename in ("output.fstats", "output.fmv", "output.geno", "output.snp", "output.ind", "merged.geno", "merged.snp", "merged.ind", "weighted.out", "transposed.geno", "transposed-lowmem.geno", "roundtrip.tgeno", "single.tgeno", "merged.tgeno", "graph.out", "reroot.out", "rolloff.out", "rolloffp.out"):
        source = work / filename
        if source.is_file():
            shutil.copyfile(source, output / filename)
    manifest["binary_roundtrip_exact"] = (work / "roundtrip.tgeno").is_file() and (work / "roundtrip.tgeno").read_bytes() == (work / "binary.tgeno").read_bytes()
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


def normalize(data, binary_dir):
    text = data.decode("utf-8", errors="replace").replace("\r\n", "\n")
    text = text.replace(binary_dir, "<BIN>").replace(binary_dir.replace("\\", "/"), "<BIN>")
    text = text.replace("<BIN>\\", "<BIN>/")
    for _, tool, _ in cases():
        text = text.replace(tool + ".exe", tool)
    text = re.sub(r"((?:version: |Version )\d+)\.w\b", r"\1", text)
    # Replace only nondeterministic values, keeping their labels and whitespace.
    text = re.sub(r"(?<=mmfaddr: )0x[0-9a-fA-F]+", "<ADDRESS>", text)
    text = re.sub(r"((?:tmp|/tmp)/(?:fsx|ppp|pops|tpar|fstpar|fslog)\.)\d+", r"\1<PID>", text)
    text = re.sub(r"[ ]*[0-9]+\.[0-9]+(?= seconds cpu)", " <CPU>", text)
    text = re.sub(r"(?<=seconds cpu)[ ]*-?[0-9]+\.[0-9]+(?= Mbytes)", " <MEMORY>", text)
    text = re.sub(r"(?<=time in dofstats:)[ ]*[0-9]+\.[0-9]+", " <CPU>", text)
    text = re.sub(r"(## end of \w+ time:)[ ]*[0-9]+\.[0-9]+", r"\1 <CPU>", text)
    text = re.sub(r"(?<=seconds memory:)[ ]*-?[0-9]+\.[0-9]+(?= Mbytes)", " <MEMORY>", text)
    text = re.sub(r"(?<=Total CPU since start:)[ ]*[0-9]+\.[0-9]+", " <CPU>", text)
    return text


def compare(left, right):
    a, b = [json.loads((directory / "manifest.json").read_text()) for directory in (left, right)]
    mismatches, matched, failed_runs = [], [], []
    diffs = []
    for name in sorted(a["cases"].keys() | b["cases"].keys()):
        ac, bc = a["cases"].get(name, {}), b["cases"].get(name, {})
        expected = 64 if name == "transpose-invalid" else 0
        if ac.get("returncode") != expected or bc.get("returncode") != expected:
            failed_runs.append({"case": name, "linux": ac, "windows": bc})
        if ac.get("returncode") != bc.get("returncode") or "returncode" not in ac or "returncode" not in bc:
            mismatches.append(name + ": exit status or unavailable")
        for stream in ("stdout", "stderr"):
            paths = [left / f"{name}.{stream}", right / f"{name}.{stream}"]
            if not all(p.is_file() for p in paths):
                continue
            x, y = [normalize(p.read_bytes(), m["binary_dir"]) for p, m in zip(paths, (a, b))]
            if x != y:
                mismatches.append(f"{name}.{stream}")
                diffs.extend(difflib.unified_diff(x.splitlines(True), y.splitlines(True), fromfile=f"linux/{name}.{stream}", tofile=f"windows/{name}.{stream}"))
            else:
                matched.append(f"{name}.{stream}")
    for filename in sorted({p.name for p in left.iterdir()} | {p.name for p in right.iterdir()}):
        if (left / filename).is_dir() or (right / filename).is_dir():
            continue
        if filename == "manifest.json" or filename.endswith((".stdout", ".stderr", ".diff", ".json")):
            continue
        x, y = left / filename, right / filename
        if not x.is_file() or not y.is_file():
            mismatches.append(f"{filename}: missing generated file")
        elif x.read_bytes() != y.read_bytes():
            mismatches.append(f"{filename}: bytes differ")
            if filename.endswith((".fstats", ".fmv", ".out")):
                diffs.extend(difflib.unified_diff(x.read_text().splitlines(True), y.read_text().splitlines(True), fromfile="linux/"+filename, tofile="windows/"+filename))
        else:
            matched.append(filename)
    result = {"matched": matched, "mismatches": mismatches, "unsuccessful_cases": failed_runs, "linux_roundtrip_exact": a["binary_roundtrip_exact"], "windows_roundtrip_exact": b["binary_roundtrip_exact"]}
    (right / "comparison.json").write_text(json.dumps(result, indent=2) + "\n")
    (right / "comparison.diff").write_text("".join(diffs))
    print(json.dumps(result, indent=2))
    return bool(mismatches or failed_runs or not a["binary_roundtrip_exact"] or not b["binary_roundtrip_exact"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bin", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--compare", type=Path, nargs=2)
    args = parser.parse_args()
    if args.compare:
        sys.exit(compare(*[p.resolve() for p in args.compare]))
    if not args.bin or not args.output:
        parser.error("use --bin and --output, or --compare")
    run(args.bin.resolve(), args.output.resolve())
