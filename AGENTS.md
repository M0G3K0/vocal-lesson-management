---
last_updated: "2026-10-03"
---

# AI作業指示

作業前に [協働ルール](docs/uncategorized/COLLABORATION-RULES.md) を読み、ユーザーの指示と合意した範囲に従う。

Pull Request本文を作成するときは、[開発フロー](docs/uncategorized/DEVELOPMENT-FLOW.md)の「Pull Requestテンプレートの利用」に従う。

## 合意済み動作確認の実行

ユーザーが合意済みの動作確認項目を実行するよう指示したときは、[run-behavior-tests Skill](.agents/skills/run-behavior-tests/SKILL.md) を使う。確認項目の提案や通常の実装検証を、このサブエージェントの自動起動理由にしない。

## 設計・仕様案のレビュー

作成担当は、具体的な設計・仕様案をユーザーに提案する直前に、[specs-review Skill](.agents/skills/specs-review/SKILL.md) を使う。通常の相談・調査・進捗報告・文面だけの修正では起動しない。レビュー担当は、この指示から別のレビュー担当を起動しない。

作成時の前提解釈に偏った見直しを避け、要求や決定事項との矛盾・漏れを別の文脈から確認し、ユーザーの判断材料を増やすために行う。

この指示に基づくレビューは読み取りと指摘の提示までとする。指摘の採用や修正はユーザーの判断に従う。ファイルへの記録、GitHubへの書き込み、commit・push・Pull Request作成・Mergeの許可を含まない。
