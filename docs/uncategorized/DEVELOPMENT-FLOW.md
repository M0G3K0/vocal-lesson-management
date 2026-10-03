---
last_updated: "2026-10-03"
---

# 開発フロー

重要：この開発フローは未完成です。現在はブランチ命名規則、Pull Requestタイトル命名規則、Pull Requestテンプレートの利用方法が記載されています。

## ブランチ命名規則

`main`以外のリモート作業ブランチは、次の形式にする。

```text
<種別>/VLM-<Issue番号>-<短い説明>
```

この形式は、ブランチ名から対象のGitHub Issue、作業の種別、作業内容を把握しやすくするために使う。対象はpush先のリモートブランチ名であり、ローカルブランチ名とは異なる名前でpushする場合も、リモート側の名前をこの形式にする。`main`はIssueごとの作業ブランチではないため、この規則の対象外とする。

種別には、作業の主目的に応じて次のいずれかを使う。

- `feat`: 利用者から見える機能の追加・拡張
- `fix`: 不具合の修正
- `refactor`: 利用者から見える動作を変えない内部構造の変更
- `test`: テストの追加・変更が主目的の作業
- `docs`: 文書だけを変更する作業
- `chore`: リポジトリ設定、ツール、依存関係、CI、開発環境などの整備

短い説明は、作業の動詞と対象が分かる表現にする。対象は新機能や作成物に限らず、修正する動作、調査対象、検証対象、文書などを含む。一般に通じる略語は使ってよい。長さの固定基準は設けない。

複数の変更を含む場合は、ブランチの主目的に合う種別を選ぶ。例えば、機能に伴うテスト追加は`feat`、不具合修正に伴う回帰テスト追加は`fix`とする。テストだけを追加・変更する作業では`test`を使う。

例：

- `feat/VLM-41-add-reservation-search`：予約検索機能を追加する
- `fix/VLM-42-handle-empty-reservation-list`：予約一覧が空の場合の動作を修正する
- `refactor/VLM-43-extract-calendar-client`：Calendar連携処理を切り出す
- `test/VLM-44-verify-route-calculation`：経路計算のテストを追加する
- `docs/VLM-45-document-branch-naming`：ブランチ命名規則を文書化する
- `chore/VLM-46-update-gradle-wrapper`：Gradle Wrapperを更新する

### Push前の形式確認

`.githooks/pre-push`は、push先のリモートブランチ名について、種別、`VLM-`に続く0より大きい数字のIssue番号、区切り、および空でない短い説明を機械的に確認する。Issue番号が実在するか、短い説明が動詞と対象を表しているかなど、説明の内容の妥当性は自動判定しない。

ブランチ名は作業内容を後から把握しやすくするための規約であり、名前が規則に合うことは変更内容の正しさを保証しない。規則違反でもマージできてよいものとし、命名違反を理由に作業を止めると開発が遅れる可能性があるため、形式確認は英語の警告にとどめる。警告の出力に失敗した場合もpushは中断しない。警告が表示するルールの詳細は、この文書を正とする。

このリポジトリでフックを有効にするには、次を一度実行する。

```sh
git config --local core.hooksPath .githooks
```

フックの振る舞いを確認するには、リポジトリのルートで次を実行する。

```sh
sh tests/pre-push-hook-test.sh
```

## Pull Requestタイトル命名規則

Pull Requestタイトルは、通常、対象のGitHub Issueタイトルに合わせ、次の形式にする。

```text
VLM-<Issue番号> <GitHub Issueのタイトル>
```

同じGitHub Issueに対する修正など、Issueタイトルと異なる変更内容を示したい場合も、この形式を使う。例えば、Issue 31に対する修正Pull Requestなら次のようにする。

```text
VLM-31 【fix】CI検査の説明を修正
```

CIは、タイトルが`VLM-<数字> <空でない説明>`の形式かを検査する。Issue番号が実在するか、説明がGitHub Issueタイトルと一致するかは検査しない。形式に合わない場合はCIを失敗させる。`main`へのマージを止めるには、GitHubのルールセット`main-pr-required`でこのチェックを必須にする。

このCIチェックの名前は`PR title validation`とする。

Pull RequestをSquash mergeしたときのコミットタイトルには、コミット数にかかわらずPull Requestタイトルを使う。

## Pull Requestテンプレートの利用

Pull Request本文は、`.github/pull_request_template.md`の項目に沿って作成する。テンプレートは`main`に含まれると、GitHub上で新しくPull Requestを作成するときに本文へ表示される。GitHub CLIで作成する場合は、次のようにテンプレートを指定する。

```sh
gh pr create --template .github/pull_request_template.md
```

AIがPull Request本文を作成するときも、このファイルを読み、各項目に沿って内容を記載する。

