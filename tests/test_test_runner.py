"""実行順、実際のプロセス出力、証跡の保持、報告の不正検知を確認する。"""

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / ".agents/skills/run-behavior-tests/scripts/report.py"
spec = importlib.util.spec_from_file_location("test_runner_report", SCRIPT)
report = importlib.util.module_from_spec(spec)
spec.loader.exec_module(report)


def case(identifier, expected="標準出力が期待どおりになる"):
    return dict(id=identifier, environment="Local", kind="その他", location="隔離したテスト環境", conditions="", action="指定したコマンドを実行する", expected=expected, notes="")


class 動作確認レポートのテスト(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="vlm-test-runner-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.run = self.root / "run"

    def initialize(self, cases=None):
        return report.initialize({"cases": cases or [case("1")]}, self.run)

    def capture(self, identifier="1", code="print('確認済み')", timeout=10):
        return report.capture(self.run, identifier, self.root, [sys.executable, "-X", "utf8", "-c", code], timeout)

    def record(self, identifier="1", status="PASS", reason=""):
        return report.record(self.run, identifier, status, "原本の標準出力を確認した", "標準出力と期待結果を照合した", reason)

    def test_記載順に実行しコマンドの原本を報告から参照できる(self):
        self.initialize([case("10"), case("2")])
        with self.assertRaisesRegex(ValueError, "10.*記録してから"):
            self.capture("2")
        marker = self.root / "order.txt"
        first_code = "from pathlib import Path; Path('order.txt').write_text('10'); print('first')"
        evidence = self.capture("10", first_code)
        metadata = report.read_json(evidence["evidence"])
        self.assertEqual(Path(evidence["evidence"]).with_name("stdout.txt").read_bytes().strip(), b"first")
        self.assertEqual(metadata["command"], [sys.executable, "-X", "utf8", "-c", first_code])
        self.assertEqual(metadata["returncode"], 0)
        self.record("10")
        self.capture("2", "from pathlib import Path; p=Path('order.txt'); assert p.read_text() == '10'; p.write_text('10,2'); print('second')")
        self.record("2")
        result = report.render(self.run)
        text = Path(result["report"]).read_text(encoding="utf-8")
        self.assertEqual(marker.read_text(), "10,2")
        self.assertLess(text.index("## No. 10"), text.index("## No. 2"))
        self.assertIn("first", text)
        self.assertIn("second", text)
        self.assertIn("evidence/001/001/stdout.txt", text)
        self.assertEqual(result["summary"]["PASS"], 2)

    def test_非ゼロ終了も失敗判定の証跡として保存する(self):
        self.initialize()
        evidence = self.capture(code="import sys; print('失敗内容', file=sys.stderr); sys.exit(7)")
        self.assertEqual(evidence["returncode"], 7)
        self.record(status="FAIL")
        result = report.render(self.run)
        self.assertEqual(result["summary"]["FAIL"], 1)
        self.assertIn("失敗内容", Path(result["report"]).read_text(encoding="utf-8"))

    def test_証跡のない成功失敗と理由のない未確認を記録できない(self):
        self.initialize()
        for status in ("PASS", "FAIL"):
            with self.subTest(status=status), self.assertRaisesRegex(ValueError, "証跡が必要"):
                self.record(status=status)
        for status in ("NOT_RUN", "UNVERIFIED"):
            with self.subTest(status=status), self.assertRaisesRegex(ValueError, "理由が必要"):
                self.record(status=status)
        self.record(status="NOT_RUN", reason="対象環境への接続先が提供されていない")
        self.assertEqual(report.render(self.run)["summary"]["NOT_RUN"], 1)

    def test_タイムアウトの途中出力を残し判定不能の理由を報告する(self):
        self.initialize()
        evidence = self.capture(code="import time; print('開始', flush=True); time.sleep(5)", timeout=0.3)
        self.assertIsNone(evidence["returncode"])
        self.assertIn("タイムアウト", evidence["error"])
        self.record(status="UNVERIFIED", reason="確認操作がタイムアウトした")
        text = Path(report.render(self.run)["report"]).read_text(encoding="utf-8")
        self.assertIn("開始", text)
        self.assertIn("判定不能", text)

    def test_タイムアウト時に子プロセスも終了し証跡を確定できる(self):
        self.initialize()
        marker = self.root / "child-finished.txt"
        child_code = (
            "from pathlib import Path; import time; "
            f"time.sleep(1.0); Path({str(marker)!r}).write_text('finished', encoding='utf-8'); "
            "print('child-finished', flush=True)"
        )
        parent_code = (
            "import subprocess,sys,time; "
            f"subprocess.Popen([sys.executable, '-c', {child_code!r}]); "
            "print('parent-started', flush=True); time.sleep(10)"
        )
        evidence = self.capture(code=parent_code, timeout=0.3)
        self.assertIsNone(evidence["returncode"])
        self.record(status="UNVERIFIED", reason="親プロセスがタイムアウトした")

        time.sleep(1.2)
        self.assertFalse(marker.exists(), "タイムアウト後も子プロセスが処理を続けている")
        report.render(self.run)
        stdout = Path(evidence["evidence"]).with_name("stdout.txt")
        self.assertNotIn(b"child-finished", stdout.read_bytes())

    def test_大きな証跡を一括読み込みせず先頭だけ報告する(self):
        self.initialize()
        source = self.root / "large.txt"
        source.write_text("あ" * 200000, encoding="utf-8")
        self.capture(code="print('確認')")
        report.attach(self.run, "1", source, "大容量ログ")
        self.record()

        with patch.object(Path, "read_bytes", side_effect=AssertionError("証跡を一括読み込みした")):
            result = report.render(self.run)

        text = Path(result["report"]).read_text(encoding="utf-8")
        self.assertIn("あ" * 4000, text)
        self.assertIn("表示は先頭4000文字です", text)

    def test_添付ファイル名の危険な拡張子を報告リンクに使わない(self):
        self.initialize()
        source = self.root / "source.md]# [injected](example)"
        source.write_bytes(b"attachment contents")
        evidence = report.attach(self.run, "1", source, "取得したファイル")
        self.record()

        artifact = Path(evidence["evidence"]).with_name("artifact.bin")
        self.assertEqual(artifact.read_bytes(), b"attachment contents")
        text = Path(report.render(self.run)["report"]).read_text(encoding="utf-8")
        self.assertIn("[artifact.bin]", text)
        self.assertNotIn("[injected]", text)

    def test_起動失敗を記録して未実施の理由を報告する(self):
        self.initialize()
        evidence = report.capture(self.run, "1", self.root, [str(self.root / "not-present.exe")])
        self.assertIsNone(evidence["returncode"])
        self.record(status="NOT_RUN", reason="コマンドを起動できなかった")
        self.assertEqual(report.render(self.run)["summary"]["NOT_RUN"], 1)

    def test_タイムアウト自体が期待結果なら照合できる(self):
        self.initialize([case("1", expected="コマンドが時間内に応答せずタイムアウトする")])
        self.capture(code="import time; time.sleep(5)", timeout=0.1)
        report.record(self.run, "1", "PASS", "0.1秒でタイムアウトした", "期待したタイムアウトをメタデータで確認した")
        self.assertEqual(report.render(self.run)["summary"]["PASS"], 1)

    def test_記録済み結果を再実行や上書きで消せない(self):
        self.initialize()
        self.capture(code="print('最初の結果')")
        self.record(status="FAIL")
        original = (self.run / "results/001.json").read_bytes()
        with self.assertRaisesRegex(ValueError, "記録済み"):
            self.capture()
        with self.assertRaisesRegex(ValueError, "記録済み"):
            self.record()
        self.assertEqual((self.run / "results/001.json").read_bytes(), original)

    def test_未記録項目と余分な結果を最終報告で見逃さない(self):
        self.initialize([case("1"), case("2")])
        self.record(status="NOT_RUN", reason="対象未提供")
        with self.assertRaisesRegex(ValueError, "2.*未記録"):
            report.render(self.run)
        self.record("2", status="NOT_RUN", reason="対象未提供")
        (self.run / "results/extra.json").write_text("{}")
        with self.assertRaisesRegex(ValueError, "対応しない結果"):
            report.render(self.run)

    def test_証跡の変更や消失を最終報告時に検知する(self):
        self.initialize()
        evidence = self.capture()
        self.record()
        stdout = Path(evidence["evidence"]).with_name("stdout.txt")
        original = stdout.read_bytes()
        stdout.write_text("後から書き換えた内容", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "原本が変更"):
            report.render(self.run)
        stdout.write_bytes(original)
        metadata = Path(evidence["evidence"])
        metadata.write_text("{}")
        with self.assertRaisesRegex(ValueError, "メタデータが変更"):
            report.render(self.run)
        metadata.unlink()
        with self.assertRaises(OSError):
            report.render(self.run)

    def test_確認項目を途中で変更できない(self):
        self.initialize()
        modified = report.read_json(self.run / "plan.json")
        modified["cases"][0]["expected"] = "実際の結果に合わせた新しい期待結果"
        (self.run / "plan.json").write_text(json.dumps(modified), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "確認項目が変更"):
            self.capture()

    def test_重複番号と種類追加と期待結果不足を開始前に拒否する(self):
        plans = [[case("1"), case("1")], [dict(case("1"), kind="CLI")], [dict(case("1"), expected="")]]
        for items in plans:
            with self.subTest(items=items), self.assertRaises(ValueError):
                self.initialize(items)
            self.assertFalse(self.run.exists())

    def test_ツール原本をコピーし取得元と対応付ける(self):
        self.initialize()
        source = self.root / "response.json"
        source.write_text('{"ready":true}', encoding="utf-8")
        evidence = report.attach(self.run, "1", source, "ローカルAPIのGET /status応答")
        self.record()
        text = Path(report.render(self.run)["report"]).read_text(encoding="utf-8")
        self.assertIn('"ready":true', text)
        self.assertIn("ローカルAPI", text)
        self.assertTrue(source.exists())
        self.assertEqual(Path(evidence["evidence"]).with_name("artifact.json").read_bytes(), source.read_bytes())

    def test_実行フォルダー外のファイルを証跡参照にできない(self):
        self.initialize()
        external = self.root / "external.txt"
        external.write_text("外部ファイル")
        with self.assertRaisesRegex(ValueError, "外部"):
            report.safe_path(self.run, "../external.txt")

    def test_出力にバッククォートがあっても報告を壊さない(self):
        self.initialize()
        self.capture(code="print('```\\nraw evidence\\n```')")
        self.record()
        text = Path(report.render(self.run)["report"]).read_text(encoding="utf-8")
        self.assertIn("````text\n```", text)

    def test_CLI経由でも引数を変えず終了コードと日本語出力を保持する(self):
        self.initialize()
        args = [sys.executable, "-B", str(SCRIPT), "capture", "--run", str(self.run), "--case", "1", "--cwd", str(self.root), "--", sys.executable, "-X", "utf8", "-c", "import sys; print(sys.argv[1]); sys.exit(3)", "空白を 含む引数"]
        outcome = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", check=False)
        self.assertEqual(outcome.returncode, 0, outcome.stderr)
        captured = json.loads(outcome.stdout)
        self.assertEqual(captured["returncode"], 3)
        self.assertEqual(Path(captured["evidence"]).with_name("stdout.txt").read_text(encoding="utf-8").strip(), "空白を 含む引数")

    def test_CP932の原本を変換せず日本語の報告を読める(self):
        self.initialize()
        code = "import sys; sys.stdout.buffer.write('日本語の証跡'.encode('cp932'))"
        evidence = report.capture(self.run, "1", self.root, [sys.executable, "-c", code], encoding="cp932")
        self.record()
        self.assertEqual(Path(evidence["evidence"]).with_name("stdout.txt").read_bytes(), "日本語の証跡".encode("cp932"))
        self.assertIn("日本語の証跡", Path(report.render(self.run)["report"]).read_text(encoding="utf-8"))

    def test_操作済みだが証跡不足の場合を未実施と混同しない(self):
        self.initialize()
        self.record(status="UNVERIFIED", reason="画面を確認したが保存手段がなかった")
        text = Path(report.render(self.run)["report"]).read_text(encoding="utf-8")
        self.assertIn("判定不能", text)
        self.assertNotIn("操作を実施していません", text)

    def test_プロセス終了前から標準出力の原本を保存する(self):
        self.initialize()
        outcome = []
        code = "from pathlib import Path; import time; print('running',flush=True);\nwhile not Path('release').exists(): time.sleep(0.02)"
        worker = threading.Thread(target=lambda: outcome.append(self.capture(code=code)))
        worker.start()
        observed = False
        try:
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline:
                files = list((self.run / 'evidence').rglob('stdout.txt'))
                if files and b'running' in files[0].read_bytes():
                    observed = True
                    break
                time.sleep(0.02)
            self.assertTrue(observed, "プロセス実行中の原本が読めない")
            self.assertTrue(worker.is_alive(), "終了後にしか原本を作っていない")
        finally:
            (self.root / 'release').touch()
            worker.join(timeout=10)
        self.assertFalse(worker.is_alive())
        self.assertEqual(outcome[0]['returncode'], 0)

    def test_同じ証跡から毎回同じ形式と内容を生成する(self):
        self.initialize()
        self.capture()
        self.record()
        first = report.render(self.run)
        original = Path(first['report']).read_bytes()
        second = report.render(self.run)
        self.assertEqual(first, second)
        self.assertEqual(original, Path(second['report']).read_bytes())
        self.assertEqual(first['unconfirmed'], [])

    def test_項目の説明にMarkdownがあっても報告の構造と混ざらない(self):
        self.initialize([case('1', expected='## 別項目\\n[偽のリンク](example.com)')])
        self.capture()
        report.record(self.run, '1', 'FAIL', '## 実際の結果', '期待と異なる')
        text = Path(report.render(self.run)['report']).read_text(encoding='utf-8')
        self.assertNotIn('\n## 実際の結果', text)
        self.assertIn('> \\#\\# 実際の結果', text)


if __name__ == "__main__":
    unittest.main()
