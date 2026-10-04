---
last_updated: "2026-10-04"
---

# GitHub Projects操作ガイド（AI向け）

この文書は、AIがGitHub Projectsを操作するときの手順とフィールド設定の判断基準を示します。GitHub ProjectsとGitHub Issueの一般的な役割を定義する文書ではありません。
また、この文書は書きかけです。今後の開発状況に応じて、AIに走査をお願いする範囲が増減する可能性があります。

現在のGitHub Projectsのフィールド名、選択肢、自動化設定は実際のProjectを正とします。この文書には、AIがそれらをどう扱うかを記載します。

## 対象Project

[Vocal Lesson Management](https://github.com/users/M0G3K0/projects/1)

## 操作の開始条件

- AIは、ユーザーから指定されたGitHub Issueや操作対象を扱います。Backlog全体から作業対象を自動で選んだり、GitHub Issueを自動でProjectに追加したりしません。
- Projectへの項目追加やフィールド更新は、ユーザーが依頼した範囲で行います。
- 関連するIssueとProjectへの書き込みをまとめ、対象と最終的な内容・フィールド値をすべて提示して一度だけ承認を求めます。そのOKで提示した書き込みすべてを実行できます。追加の承認を重ねません。承認後に対象や内容が変わった場合は、変更分について確認します。
- Projectを読み取れない、または操作できない場合は、その事実を伝え、読み取れたものとして扱いません。

## フィールドの扱い

### Status

- Statusは作業の進捗を表し、選択肢は`Todo`、`In Progress`、`Done`です。`Waiting`は使いません。
- Statusは作業の区切りで更新し、開発フローの各段階ごとに更新する必要はありません。
- `In Progress`にする時点は人間が判断します。AIは独自の基準で開始時点を決めません。
- Projectに設定された自動化を確認し、追加時やIssueのClose時にStatusが自動更新された場合は、その結果を尊重します。

### Priority

- 選択肢は`High`、`Medium`、`Low`です。
- Priorityの既定値は`Medium`です。
- Issueの内容からPriorityを推測・自動設定しません。変更する場合はユーザーの指示に従います。

### Sprint

- SprintはProjectのIterationフィールドで管理し、名前は`S001`の形式にします。
- Sprintは1週間単位です。開始日などの現在のIteration設定は実際のProjectを正とします。
- IssueをSprint未設定のBacklogに置くことができます。AIは内容や日付からSprintを自動で割り当てたり、Issueを別Sprintへ移動したりしません。
- Sprintの割り当てや移動は、ユーザーが指定した場合に行います。利用可能なIterationは実際のProject設定を確認します。

### Label

- GitHub Projectsの`Labels`フィールドには、紐づくGitHub Issueに設定されたLabelが表示されます。
- Labelは必須ではありません。
- Issueの内容からLabelを自動判定しません。付与はユーザーの指示に従い、Repository上の正式名称を確認して使用します。

### Title、Parent issue、Updated

- `Title`は紐づくGitHub Issueのタイトルです。Project上で独立したタイトルとして変更しません。
- Parent issueの関係は、ユーザーが指定した親子関係を使います。Issueの内容だけから親子関係を推測して変更しません。
- `Updated`はGitHub Projectsが管理する値です。AIは手動で設定しません。

## Status自動化

- 現在有効な自動化は、`Item added to project`でStatusを`Todo`へ、`Item closed`で`Done`へ更新するものです。どちらもIssueとPull Requestが対象です。
- これらはProjectに追加済みのitemのStatusを更新する自動化です。RepositoryからIssueを自動追加する`Auto-add to project`とは別の機能で、後者は現在無効です。
- `Item reopened`の自動化は現在無効です。有効にした場合の設定値は`In Progress`であり、Reopen時に`Todo`へ戻るとは仮定しません。
- AIは実際のProject設定と操作後の値を確認し、自動化の結果を手動操作で上書きしません。設定や実際の動作がこの記載と異なる場合は、ユーザーに伝えます。
