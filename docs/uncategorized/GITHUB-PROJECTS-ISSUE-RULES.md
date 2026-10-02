---
last_updated: "2026-10-03"
---

# GitHub Projects・GitHub Issue運用ルール（暫定）

この文書は、GitHub ProjectsとGitHub Issueの役割・運用方法を記録するものです。

## GitHub Projectsの役割

- GitHub Projectsは、draft issueとGitHub Issueの所在・状態を管理する。
- 未整理の着想はdraft issueとして扱う。
- 議論・判断・作業が必要になった着想はGitHub Issueへ変換する。

## GitHub Issueの役割

- GitHub Issueは、解決すべき一つの目的を扱う。
- 調査、意思決定、ドキュメント作成・更新、設計、実装、バグ修正を扱える。
- 大きな目的は、親GitHub IssueとGitHub sub-issueに分割できる。
- GitHub Issueには、議論や意思決定に至る経緯を残す。

## GitHub Projectsのフィールド

### Status

Statusは作業の進捗を表す。

- `Todo`
- `In Progress`
- `Done`

ブロックや合意待ちはStatusに追加せず、GitHub Issueのコメントなどに記録する。Statusは作業の区切りで更新する。

根拠：Statusの種類を増やすと、進捗と作業上の事情が混ざり、更新の負担も増えるため。

### Priority

PriorityはGitHub Projectsの単一選択フィールドで管理する。

- `High`
- `Medium`
- `Low`

既存のProject項目は`Medium`に設定する。新規項目も原則`Medium`とし、必要な場合だけ手動で変更する。Priorityの自動判定や自動設定は行わない。

根拠：優先度はStatusやSprintとは異なる情報であり、手動判断を自動分類で置き換えないため。

### Sprint

SprintはGitHub ProjectsのIterationフィールドで管理する。

- 期間：1週間
- 範囲：`S001`〜`S005`
- `S001`の開始日：2026年10月3日
- Sprintへの割り当て：手動
- 未完了項目の移動：手動

日付を理由にIssueのSprint割り当てを自動変更しない。

根拠：1週間単位で作業量を調整しつつ、予定外の自動移動による誤った計画変更を避けるため。

## GitHub ProjectsのView

### Backlog

- `Done`以外の項目を表示する。
- Sprint単位でグループ化する。
- Sprint未設定の項目も表示する。
- 表示列は`Parent issue`、`Title`、`Status`、`Priority`、`Updated`とする。

### All

- 完了済みを含む全項目を表示する。
- 表示列はBacklogと同じにする。

根拠：日々の作業対象と、完了済みを含む全体確認を分けることで、Backlogを簡潔に保つため。

## GitHub IssueのLabel

Labelは必須にしない。

現時点では、GitHubの既定Labelである`bug`だけを運用対象とする。該当するIssueが発生した場合に付ける。現在のIssueには付けない。

根拠：Labelによる分類が必要なIssueだけを対象にし、使わない分類を先に増やさないため。

## GitHub Issueテンプレート

Issue作成時に、標準IssueテンプレートまたはBlank issueを選べるようにする。

標準Issueテンプレートの本文には、次の二つのセクションだけを置く。

- これはなに
- 完了条件

Blank issueも選択できるようにし、標準形式をすべてのIssueに強制しない。要求書や仕様書が存在する場合は、それらを正とする。

根拠：二つのセクションで標準的なIssueの内容と完了判断を簡潔に記載できる一方、Blank issueを残すことで個別の事情に合わない形式を強制せずに済むため。

## 自動化

次の標準ワークフローを利用する。

- Project項目が追加されたらStatusを`Todo`にする。
- GitHub IssueがCloseされたらStatusを`Done`にする。

次の自動化は行わない。

- GitHub Issueの自動追加
- GitHub sub-issueの自動追加
- Pull Requestとの自動連動
- Reopen時のStatus自動変更
- Priorityの自動設定
- Issue内容からの自動分類
- Sprintの自動割り当て・自動移動

根拠：作業の追加や分類を自動化すると、意図しないProject更新や作業計画の変更が起きるため。Close時のDoneだけは、Issueの状態とProjectの進捗を一致させるために利用する。
