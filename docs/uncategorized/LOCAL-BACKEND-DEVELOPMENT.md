---
last_updated: "2026-10-05"
---

# バックエンドのローカル開発環境

この文書は、GitHub Issue [#47](https://github.com/M0G3K0/vocal-lesson-management/issues/47)で構築するバックエンドのローカル開発環境と、その再現手順を記録する。

## 構成

バックエンドは、`backend/`以下のGradleマルチプロジェクトとして構成する。

```text
backend/
├── web/        Spring BootアプリケーションとHTTP APIの入口
├── usecase/    アプリケーション処理と外部接続の契約
├── domain/     業務モデルと業務ルール
├── infra/      DB・外部サービスへの接続実装
└── infra-orm/  FlywayとjOOQのコード生成基盤
```

各モジュールの責務は、[バックエンドのアプリケーションアーキテクチャ](./BACKEND-ARCHITECTURE.md)に従う。

## 採用バージョン

| 対象 | バージョン・条件 |
| --- | --- |
| JDK | 21 |
| Spring Boot | 3.5.16 |
| Spring Web MVC | Spring Boot 3.5.16の依存関係管理に従う |
| Gradle | Gradle Wrapper 8.14系 |
| Kotlin | 1.9.25 |
| PostgreSQL | 17系のDockerイメージ |
| Flyway | Spring Boot 3.5.16の依存関係管理に従う |
| jOOQ | 3.19.35 |
| JUnit Jupiter | Spring Boot 3.5.16の依存関係管理に従う |
| MockK | 1.13.17 |

バージョンを変更する場合は、互換性を確認したうえでGradle設定とこの表を同じ変更に含める。

## 前提

次のツールをローカルに用意する。

- JDK 21
- Docker Desktopなど、Docker Composeを実行できる環境

Gradleはリポジトリ内のGradle Wrapperを使う。グローバルにGradleをインストールする必要はない。

Windows Git Bashを使う場合は、JDK 21とDocker CLIをGit Bashから参照できる状態にする。

```bash
java -version
docker --version
```

`java`が見つからない場合は、JDK 21のインストール先を`JAVA_HOME`に設定し、`bin`をPATHへ追加する。`<JDK 21のインストール先>`は、実際の環境に合わせて置き換える。

```bash
export JAVA_HOME="<JDK 21のインストール先>"
export PATH="$JAVA_HOME/bin:$PATH"
```

Docker Desktopの標準的なインストール先を使っていて、`docker`が見つからない場合は、次のようにDocker CLIの場所をPATHへ追加する。インストール先を変更している場合は、その場所に置き換える。

```bash
export PATH="/c/Program Files/Docker/Docker/resources/bin:$PATH"
```

## 初回セットアップ

リポジトリのルートで実行する。

### PostgreSQLを起動する

Windows PowerShell:

```powershell
docker compose -f backend/compose.yaml up -d
```

macOS・Linux:

```sh
docker compose -f backend/compose.yaml up -d
```

Windows Git Bash:

```bash
docker compose -f backend/compose.yaml up -d
```

PostgreSQLのローカル接続情報は次のとおり。いずれもローカル開発専用の初期値であり、本番環境の認証情報として使わない。

```text
URL:      jdbc:postgresql://localhost:5432/vocal_lesson_management
ユーザー: vocal_lesson_management
パスワード: local_development_only
```

別の接続情報を使う場合は、次の環境変数で上書きする。

- `VLM_DB_URL`
- `VLM_DB_USER`
- `VLM_DB_PASSWORD`
- `VLM_SERVER_PORT`

### ビルドとテストを実行する

Windows PowerShell:

```powershell
backend\gradlew.bat --project-dir backend build
backend\gradlew.bat --project-dir backend test
```

macOS・Linux:

```sh
./backend/gradlew --project-dir backend build
./backend/gradlew --project-dir backend test
```

Windows Git Bash:

```bash
./backend/gradlew.bat --project-dir backend build
./backend/gradlew.bat --project-dir backend test
```

### Flywayのマイグレーションを実行する

Flywayは、Spring Bootアプリケーションの起動時に実行する。

Windows PowerShell:

```powershell
backend\gradlew.bat --project-dir backend :web:bootRun
```

macOS・Linux:

```sh
./backend/gradlew --project-dir backend :web:bootRun
```

Windows Git Bash:

```bash
./backend/gradlew.bat --project-dir backend :web:bootRun
```

起動ログにアプリケーションが起動したことが表示されるまで待つ。確認後、`Ctrl+C`でアプリケーションを終了する。マイグレーションSQLは`backend/infra-orm/src/main/resources/db/migration/`に置く。

### jOOQのコードを生成する

PostgreSQLが起動し、Flywayのマイグレーションが適用された状態で実行する。

現在は、生成コードを参照する業務コードがないため、必要なときにこのタスクを明示的に実行する。

Windows PowerShell:

```powershell
backend\gradlew.bat --project-dir backend :infra-orm:jooqCodegen
```

macOS・Linux:

```sh
./backend/gradlew --project-dir backend :infra-orm:jooqCodegen
```

Windows Git Bash:

```bash
./backend/gradlew.bat --project-dir backend :infra-orm:jooqCodegen
```

生成コードは`backend/infra-orm/build/generated-src/jooq/main/`に出力される。このディレクトリはビルド生成物として扱い、Gitには追加しない。

## 終了

Windows PowerShell:

```powershell
docker compose -f backend/compose.yaml down
```

macOS・Linux:

```sh
docker compose -f backend/compose.yaml down
```

Windows Git Bash:

```bash
docker compose -f backend/compose.yaml down
```

DBデータも削除して初期状態に戻す場合は、`down`に`-v`を追加する。

```text
docker compose -f backend/compose.yaml down -v
```

## この環境で確認できること

- 5つのGradleモジュールをまとめてビルドできる。
- Spring Bootアプリケーションを起動できる。
- PostgreSQLをDocker Composeで起動できる。
- Spring Bootの起動時にFlywayのマイグレーションを適用できる。
- PostgreSQLのスキーマを入力としてjOOQのコード生成を実行できる。
- JUnit Jupiterによるテストを実行できる。
- MockKをテスト依存関係として利用できる。

具体的な業務モデル、API、DBテーブルは、機能ごとの要求・仕様が決まった後に追加する。
