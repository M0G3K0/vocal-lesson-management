"""動作確認の順序・証跡・結果を検査し、同じ形式の報告を作る（標準ライブラリのみ）。"""

import argparse
from collections import Counter
import codecs
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import shutil
import subprocess
import sys


# 入力検査と公開JSON Schemaで、フィールドの定義を共有する。
CASE_FIELDS = {
    "id": (None, False),
    "environment": (("Local", "Prev", "Prd"), False),
    "kind": (("Web", "API", "その他"), False),
    "location": (None, False),
    "conditions": (None, True),
    "action": (None, False),
    "expected": (None, False),
    "notes": (None, True),
}
RESULT_FIELDS = {
    "case_id": (None, False),
    "status": (("PASS", "FAIL", "NOT_RUN", "UNVERIFIED"), False),
    "actual": (None, False),
    "comparison": (None, False),
    "reason": (None, True),
    "notes": (None, True),
}
STATUS_LABELS = {"PASS": "成功", "FAIL": "失敗", "NOT_RUN": "未実施", "UNVERIFIED": "判定不能"}


def now():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def digest(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def read_preview(path, encoding, limit=4000):
    decoder = codecs.getincrementaldecoder(encoding)(errors="replace")
    chunks = []
    character_count = 0
    with Path(path).open("rb") as stream:
        while True:
            raw = stream.read(4096)
            finished = not raw
            decoded = decoder.decode(raw, final=finished)
            if decoded:
                remaining = limit + 1 - character_count
                if remaining > 0:
                    excerpt = decoded[:remaining]
                    chunks.append(excerpt)
                    character_count += len(excerpt)
                if character_count > limit:
                    return "".join(chunks)[:limit], True
            if finished:
                return "".join(chunks), False


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, value):
    # 証跡と結果を上書きせず、過去の失敗を消せないようにする。
    with Path(path).open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def validate_fields(value, fields, label):
    if not isinstance(value, dict) or set(value) != set(fields):
        raise ValueError(f"{label}: フィールドは {', '.join(fields)} に一致させてください")
    for key, (choices, empty_allowed) in fields.items():
        text = value[key]
        if not isinstance(text, str) or (not empty_allowed and not text.strip()):
            raise ValueError(f"{label}.{key}: 有効な文字列が必要です")
        if choices is not None and text not in choices:
            raise ValueError(f"{label}.{key}: {', '.join(choices)} のいずれかにしてください")


def validate_plan(plan):
    if not isinstance(plan, dict) or set(plan) != {"cases"}:
        raise ValueError("入力JSONには cases 配列だけを記載してください")
    if not isinstance(plan["cases"], list) or not plan["cases"]:
        raise ValueError("cases には1件以上の確認項目が必要です")
    identifiers = set()
    for case in plan["cases"]:
        validate_fields(case, CASE_FIELDS, "確認項目")
        if case["id"] in identifiers:
            raise ValueError(f"項目番号が重複しています: {case['id']}")
        identifiers.add(case["id"])


def initialize(plan, run):
    validate_plan(plan)
    run = Path(run).resolve()
    run.mkdir(parents=True, exist_ok=False)
    (run / "results").mkdir()
    (run / "evidence").mkdir()
    write_json(run / "plan.json", plan)
    write_json(run / "run.json", {"version": 1, "started_at": now(), "plan_sha256": digest(run / "plan.json")})
    return run


def load_run(run):
    run = Path(run).resolve()
    metadata = read_json(run / "run.json")
    if metadata.get("version") != 1 or digest(run / "plan.json") != metadata.get("plan_sha256"):
        raise ValueError("開始時の確認項目が変更されています")
    plan = read_json(run / "plan.json")
    validate_plan(plan)
    return run, plan, metadata


def case_position(plan, case_id):
    for index, case in enumerate(plan["cases"], 1):
        if case["id"] == case_id:
            return index
    raise ValueError(f"合意済み項目にない番号です: {case_id}")


def result_path(run, index):
    return run / "results" / f"{index:03}.json"


def current_case(run, plan, case_id):
    index = case_position(plan, case_id)
    if result_path(run, index).exists():
        raise ValueError(f"項目 {case_id} は記録済みです。再実行には新しい実行フォルダーを使ってください")
    for previous in range(1, index):
        if not result_path(run, previous).exists():
            raise ValueError(f"項目 {plan['cases'][previous - 1]['id']} を記録してから次へ進んでください")
    return index


def new_evidence(run, index):
    parent = run / "evidence" / f"{index:03}"
    parent.mkdir(exist_ok=True)
    numbers = [int(path.name) for path in parent.iterdir() if path.is_dir() and path.name.isdigit()]
    folder = parent / f"{max(numbers, default=0) + 1:03}"
    folder.mkdir()
    return folder


def file_info(path):
    return {"name": path.name, "sha256": digest(path)}


def terminate_process_tree(process):
    if os.name == "nt":
        # Ctrl-Break reaches all processes in the isolated group; taskkill is the hard-kill fallback.
        try:
            process.send_signal(signal.CTRL_BREAK_EVENT)
        except OSError:
            pass
        try:
            process.wait(timeout=0.5)
        except subprocess.TimeoutExpired:
            outcome = subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
            if outcome.returncode != 0:
                if process.poll() is None:
                    process.kill()
                    process.wait()
                raise OSError(f"taskkill failed to terminate process tree {process.pid}")
        return

    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    except OSError:
        if process.poll() is None:
            process.kill()
            process.wait()
        raise

    try:
        process.wait(timeout=0.5)
    except subprocess.TimeoutExpired:
        pass

    # The group leader may exit on SIGTERM while a child remains alive.
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    except OSError:
        if process.poll() is None:
            process.kill()
            process.wait()
        raise
    process.wait()


def capture(run, case_id, cwd, command, timeout=60, encoding="utf-8"):
    run, plan, _ = load_run(run)
    index = current_case(run, plan, case_id)
    cwd = Path(cwd).resolve(strict=True)
    if not cwd.is_dir() or not command or timeout <= 0:
        raise ValueError("実行場所、コマンド、正のタイムアウトを指定してください")
    codecs.lookup(encoding)
    folder = new_evidence(run, index)
    metadata = {"kind": "command", "case_id": case_id, "command": command, "cwd": str(cwd), "encoding": encoding, "started_at": now()}
    # 終了後にAIが再構成せず、プロセスから原本へ直接書く。大きな出力もメモリに蓄えない。
    with (folder / "stdout.txt").open("xb") as stdout, (folder / "stderr.txt").open("xb") as stderr:
        process_options = {}
        if os.name == "nt":
            process_options["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
        else:
            process_options["start_new_session"] = True
        try:
            process = subprocess.Popen(command, cwd=cwd, stdout=stdout, stderr=stderr, **process_options)
        except OSError as error:
            metadata.update(returncode=None, error=str(error))
        else:
            try:
                returncode = process.wait(timeout=timeout)
                metadata.update(returncode=returncode, error="")
            except subprocess.TimeoutExpired:
                terminate_process_tree(process)
                metadata.update(returncode=None, error=f"{timeout}秒でタイムアウトしました")
    metadata["finished_at"] = now()
    metadata["files"] = [file_info(folder / name) for name in ("stdout.txt", "stderr.txt")]
    write_json(folder / "metadata.json", metadata)
    return {"evidence": str(folder / "metadata.json"), "returncode": metadata["returncode"], "error": metadata["error"]}


def attach(run, case_id, source, label, encoding="utf-8"):
    run, plan, _ = load_run(run)
    index = current_case(run, plan, case_id)
    source = Path(source).resolve(strict=True)
    if not source.is_file() or not label.strip():
        raise ValueError("証跡の原本ファイルと取得元の説明が必要です")
    codecs.lookup(encoding)
    folder = new_evidence(run, index)
    suffix = source.suffix.lower()
    if not re.fullmatch(r"\.[a-z0-9]{1,10}", suffix):
        suffix = ".bin"
    target = folder / ("artifact" + suffix)
    shutil.copyfile(source, target)
    write_json(folder / "metadata.json", {"kind": "artifact", "case_id": case_id, "label": label, "encoding": encoding, "captured_at": now(), "files": [file_info(target)]})
    return {"evidence": str(folder / "metadata.json")}


def safe_path(run, relative):
    candidate = Path(relative)
    if candidate.is_absolute():
        raise ValueError("証跡の参照は実行フォルダーからの相対パスにしてください")
    target = (run / candidate).resolve(strict=True)
    if not target.is_relative_to(run) or not target.is_file():
        raise ValueError("証跡が実行フォルダーの外部を参照しています")
    return target


def check_evidence(run, entry, case_id):
    if not isinstance(entry, dict) or set(entry) != {"path", "sha256"}:
        raise ValueError("証跡参照の形式が不正です")
    path = safe_path(run, entry["path"])
    if digest(path) != entry["sha256"]:
        raise ValueError("保存済み証跡のメタデータが変更されています")
    metadata = read_json(path)
    if metadata.get("case_id") != case_id or metadata.get("kind") not in ("command", "artifact"):
        raise ValueError("別の項目、または不明な種類の証跡です")
    codecs.lookup(metadata.get("encoding", "utf-8"))
    files = metadata.get("files")
    if not isinstance(files, list) or not files:
        raise ValueError("証跡の原本ファイルがありません")
    for entry in files:
        if not isinstance(entry, dict) or set(entry) != {"name", "sha256"} or Path(entry["name"]).name != entry["name"]:
            raise ValueError("証跡のファイル参照が不正です")
        original = safe_path(run, (path.parent / entry["name"]).relative_to(run))
        if digest(original) != entry["sha256"]:
            raise ValueError(f"証跡の原本が変更されています: {original.name}")
    if metadata["kind"] == "command":
        if {file["name"] for file in files} != {"stdout.txt", "stderr.txt"}:
            raise ValueError("コマンドの出力ファイルが不足しています")
        if not isinstance(metadata.get("command"), list) or not metadata["command"]:
            raise ValueError("実行コマンドが記録されていません")
        # 起動エラーやタイムアウト自体を確認する項目もあり得る。
        # 期待と一致するかは実行担当が照合し、ここでは観察の記録があることを検査する。
        observed = isinstance(metadata.get("returncode"), int) or bool(metadata.get("error"))
    else:
        observed = bool(metadata.get("label", "").strip())
    return path, metadata, observed


def collect_evidence(run, index, case_id):
    parent = run / "evidence" / f"{index:03}"
    if not parent.exists():
        return []
    entries = []
    for folder in sorted(parent.iterdir()):
        if not folder.is_dir():
            raise ValueError("証跡フォルダーの構造が不正です")
        path = folder / "metadata.json"
        entry = {"path": path.relative_to(run).as_posix(), "sha256": digest(path)}
        check_evidence(run, entry, case_id)
        entries.append(entry)
    return entries


def record(run, case_id, status, actual, comparison, reason="", notes=""):
    run, plan, _ = load_run(run)
    index = current_case(run, plan, case_id)
    result = dict(case_id=case_id, status=status, actual=actual, comparison=comparison, reason=reason, notes=notes)
    validate_fields(result, RESULT_FIELDS, "結果")
    result["evidence"] = collect_evidence(run, index, case_id)
    validate_result(run, result, case_id)
    write_json(result_path(run, index), result)
    return {"case_id": case_id, "status": status, "evidence_count": len(result["evidence"])}


def validate_result(run, result, case_id):
    if not isinstance(result, dict) or set(result) != set(RESULT_FIELDS) | {"evidence"}:
        raise ValueError("結果のフィールドが不正です")
    validate_fields({key: result[key] for key in RESULT_FIELDS}, RESULT_FIELDS, "結果")
    if result["case_id"] != case_id or not isinstance(result["evidence"], list):
        raise ValueError("結果の項目番号または証跡一覧が不正です")
    observed = any([check_evidence(run, entry, case_id)[2] for entry in result["evidence"]])
    if result["status"] in ("PASS", "FAIL") and not observed:
        raise ValueError("成功・失敗の判定には、操作した結果の証跡が必要です")
    if result["status"] in ("NOT_RUN", "UNVERIFIED") and not result["reason"].strip():
        raise ValueError("未実施・判定不能の理由が必要です")


def code_block(text):
    # 出力にMarkdownのフェンスが含まれていても報告を壊さない。
    fence = "```"
    while fence in text:
        fence += "`"
    return f"{fence}text\n{text}\n{fence}"


def plain_text(text):
    return re.sub(r"([\\`*_{}\[\]<>#+!|])", r"\\\1", text)


def quoted_text(text):
    return "\n".join("> " + plain_text(line) for line in text.splitlines())


def render(run):
    run, plan, metadata = load_run(run)
    results = []
    for index, case in enumerate(plan["cases"], 1):
        path = result_path(run, index)
        if not path.exists():
            raise ValueError(f"項目 {case['id']} の結果が未記録です")
        result = read_json(path)
        validate_result(run, result, case["id"])
        if result["evidence"] != collect_evidence(run, index, case["id"]):
            raise ValueError("記録済み結果と証跡一覧が一致しません")
        results.append(result)
    if len(list((run / "results").iterdir())) != len(results):
        raise ValueError("合意済み項目に対応しない結果ファイルがあります")
    counts = Counter(result["status"] for result in results)
    summary = {status: counts[status] for status in STATUS_LABELS}
    lines = ["# 動作確認結果", "", f"開始日時: {metadata['started_at']}", "", f"確認項目: {len(results)}件", "", " / ".join(f"{status}（{STATUS_LABELS[status]}）: {counts[status]}件" for status in STATUS_LABELS), ""]
    for case, result in zip(plan["cases"], results):
        identifier = plain_text(case["id"]).replace("\r", " ").replace("\n", " ")
        lines += [f"## No. {identifier}", "", f"**判定: {result['status']}（{STATUS_LABELS[result['status']]}）**", ""]
        for label, value in (("環境", case["environment"]), ("種類", case["kind"]), ("場所", case["location"]), ("条件", case["conditions"] or "なし"), ("なにをする", case["action"]), ("どうなってほしい", case["expected"]), ("実際の結果", result["actual"]), ("照合", result["comparison"]), ("その他結果", "\n".join(text for text in (case["notes"], result["notes"]) if text) or "なし")):
            lines += [f"**{label}**", "", quoted_text(value), ""]
        if result["reason"]:
            lines += ["**未実施・判定不能の理由**", "", quoted_text(result["reason"]), ""]
        lines += ["**証跡**", ""]
        if not result["evidence"]:
            lines += ["保存された証跡なし", ""]
        for number, entry in enumerate(result["evidence"], 1):
            path, evidence, _ = check_evidence(run, entry, case["id"])
            lines += [f"証跡 {number}: [メタデータ]({entry['path']})", ""]
            if evidence["kind"] == "command":
                lines += ["コマンド引数:", "", code_block(json.dumps(evidence["command"], ensure_ascii=False)), "", f"実行場所: `{evidence['cwd']}`", "", f"終了コード: `{evidence['returncode']}` / 実行エラー: {evidence['error'] or 'なし'}", "", f"実行時刻: {evidence['started_at']} → {evidence['finished_at']}", ""]
            else:
                lines += ["取得元・観察対象:", "", quoted_text(evidence['label']), "", f"保存時刻: {evidence['captured_at']}", ""]
            for file in evidence["files"]:
                original = path.parent / file["name"]
                relative = original.relative_to(run).as_posix()
                lines += [f"原本: [{file['name']}]({relative})", ""]
                if original.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"):
                    lines += [f"![証跡]({relative})", ""]
                elif original.suffix.lower() in (".txt", ".json", ".html", ".csv", ".log"):
                    text, truncated = read_preview(original, evidence.get("encoding", "utf-8"))
                    lines += [code_block(text or "（出力なし）"), ""]
                    if truncated:
                        lines += ["表示は先頭4000文字です。全文は原本リンクから確認してください。", ""]
    report = run / "report.md"
    report.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    (run / "report.json").write_text(json.dumps({"cases": plan["cases"], "results": results, "summary": summary}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    unconfirmed = [{"case_id": result["case_id"], "status": result["status"], "reason": result["reason"]} for result in results if result["status"] in ("NOT_RUN", "UNVERIFIED")]
    return {"report": str(report), "summary": summary, "unconfirmed": unconfirmed}


def object_schema(fields):
    properties = {}
    for key, (choices, empty_allowed) in fields.items():
        properties[key] = {"type": "string"}
        if choices is not None:
            properties[key]["enum"] = list(choices)
        if not empty_allowed:
            properties[key]["minLength"] = 1
    return {"type": "object", "properties": properties, "required": list(fields), "additionalProperties": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="operation", required=True)
    schema = subcommands.add_parser("schema")
    schema.add_argument("--kind", choices=("plan", "result"), required=True)
    for operation in ("init", "capture", "attach", "record", "render"):
        command = subcommands.add_parser(operation)
        command.add_argument("--run", required=True)
        if operation in ("capture", "attach", "record"):
            command.add_argument("--case", required=True)
        if operation in ("capture", "attach"):
            command.add_argument("--encoding", default="utf-8", help="保存した出力を表示するときの文字コード。原本は変換しません")
        if operation == "init":
            command.add_argument("--plan", required=True)
        elif operation == "capture":
            command.add_argument("--cwd", required=True)
            command.add_argument("--timeout", type=float, default=60)
            command.add_argument("command", nargs=argparse.REMAINDER)
        elif operation == "attach":
            command.add_argument("--source", required=True)
            command.add_argument("--label", required=True)
        elif operation == "record":
            command.add_argument("--status", required=True, choices=tuple(STATUS_LABELS))
            command.add_argument("--actual", required=True)
            command.add_argument("--comparison", required=True)
            command.add_argument("--reason", default="")
            command.add_argument("--notes", default="")
    args = parser.parse_args()
    if args.operation == "schema":
        output = object_schema(CASE_FIELDS if args.kind == "plan" else RESULT_FIELDS)
        if args.kind == "plan":
            output = {"type": "object", "properties": {"cases": {"type": "array", "minItems": 1, "items": output}}, "required": ["cases"], "additionalProperties": False}
    elif args.operation == "init":
        plan = json.load(sys.stdin) if args.plan == "-" else read_json(args.plan)
        output = {"run": str(initialize(plan, args.run))}
    elif args.operation == "capture":
        command = args.command[1:] if args.command[:1] == ["--"] else args.command
        output = capture(args.run, args.case, args.cwd, command, args.timeout, args.encoding)
    elif args.operation == "attach":
        output = attach(args.run, args.case, args.source, args.label, args.encoding)
    elif args.operation == "record":
        output = record(args.run, args.case, args.status, args.actual, args.comparison, args.reason, args.notes)
    else:
        output = render(args.run)
    print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    try:
        main()
    except (ValueError, OSError, KeyError, TypeError, LookupError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)
