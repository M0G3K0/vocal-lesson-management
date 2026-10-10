---
last_updated: "2026-10-08"
---

# ローカル設定と秘密情報の扱い

## 目的

フロントエンドとバックエンドで共通する、ローカル設定と秘密情報の扱いを定める。

各環境の具体的な準備手順は、次の文書から参照する。

- [フロントエンドのローカル開発環境](./LOCAL-FRONTEND-DEVELOPMENT.md)
- [バックエンドのローカル開発環境](./LOCAL-BACKEND-DEVELOPMENT.md)

## 設定の渡し方

アプリケーションへ渡すローカル設定の正は、起動するプロセスの環境変数とする。

- Spring BootやAngularのソースコードへ、個人の設定値を直接書かない。
- 設定値を必要とするプロセスの起動時に、そのプロセスの環境変数として渡す。
- 環境変数の名前は、実装とこの文書の記載を一致させる。
- アプリケーションがルートの`.env`を自動的に読み込むことは前提にしない。

ルートの`.env`は、ローカルで設定値を管理するための任意のファイルとして利用できる。

- `.env.example`を設定名と安全な例の参照元とする。
- 実際の値を使う場合は、`.env.example`を`.env`へコピーして編集する。
- `.env`の値をプロセスへ渡す方法は、起動するツールやシェルの手順に従う。
- `.env`を使わず、IDEやシェルの環境変数設定へ直接登録してもよい。

現在のローカル開発では、設定例に記載した値が安全なローカル専用の初期値として実装されているため、`.env`を作成しなくても準備できる。

### Docker Composeへ渡す場合

`.env`を使う場合は、リポジトリルートから`--env-file`で明示的に指定する。

```bash
docker compose --env-file .env -f backend/compose.yaml up -d
```

`.env`を使わない場合は、`--env-file .env`を省略する。環境変数も設定していなければ、バックエンドのローカル開発手順に記載された安全な初期値が使われる。

### 既存DBのユーザー名・パスワードを変更する場合

PostgreSQLのユーザー名・パスワードの初期設定は、データディレクトリが空の場合にだけ適用される。
既存の`postgres-data` Volumeがある状態で`VLM_DB_USER`や`VLM_DB_PASSWORD`を変更しても、DB内の認証情報は更新されない。

ローカルDBのデータを削除してよい場合は、次の順序で再作成する。

1. Spring Bootを停止する。
2. 次のコマンドでコンテナとVolumeを削除する。**ローカルDBの全データが削除される。**

   ```bash
   docker compose --env-file .env -f backend/compose.yaml down -v
   ```

3. `.env`の`VLM_DB_USER`と`VLM_DB_PASSWORD`を変更する。
4. 新しい認証情報でPostgreSQLを初期化する。

   ```bash
   docker compose --env-file .env -f backend/compose.yaml up -d
   ```

5. Spring Bootにも同じユーザー名・パスワードを環境変数として渡して起動する。`.env`を変更するだけではSpring Bootへは渡らない。

データを保持する必要がある場合は、この再作成手順を実行しない。DB内のユーザー・パスワードの変更と、接続元の設定変更を別途行う。

[PostgreSQL公式Dockerイメージの環境変数の説明](https://github.com/docker-library/docs/blob/master/postgres/content.md#environment-variables)

### Spring Bootへ渡す場合

Spring Bootは起動プロセスの環境変数を読む。シェルまたはIDEの実行設定へ、必要な変数を登録してから起動する。

Git Bashの例：

```bash
VLM_SERVER_PORT=8081 ./backend/gradlew.bat --project-dir backend :web:bootRun
```

PowerShellの例：

```powershell
$env:VLM_SERVER_PORT = "8081"
backend\gradlew.bat --project-dir backend :web:bootRun
Remove-Item Env:VLM_SERVER_PORT
```

この例ではDBの認証情報を変更せず、待ち受けポートだけを8081へ変更する。PowerShellではSpring Bootを停止した後、最後のコマンドで環境変数を解除する。

## 設定例

リポジトリルートの[`.env.example`](../../.env.example)を参照する。

現在記載している設定は、バックエンドとローカルPostgreSQLに関するものである。

- `VLM_DB_URL`
  - Spring Bootが接続するデータベースのURL。
- `VLM_DB_USER`
  - Spring BootとローカルPostgreSQLが使用するユーザー名。
- `VLM_DB_PASSWORD`
  - Spring BootとローカルPostgreSQLが使用するローカル開発用パスワード。
- `VLM_SERVER_PORT`
  - Spring Bootが待ち受けるポート番号。

`local_development_only`はローカル開発専用の固定値であり、実際のサービスの認証情報や本番環境のパスワードとして使用しない。

## フロントエンドへ渡す設定

ブラウザへ渡された値は利用者から確認できるため、フロントエンドへ渡してよい設定と秘密情報を分ける。

- APIの接続先など、ブラウザへ公開してよい値だけをフロントエンドへ渡す。
- パスワード、Cookie、OAuthトークン、APIキーなどの秘密情報をフロントエンドへ渡さない。
- 秘密情報を必要とする外部サービスへの接続は、バックエンド側で扱う。

現在、フロントエンドへ渡すローカル設定はない。

## Gitでの扱い

実値を含むローカル設定ファイルはGit管理対象にしない。

- `.env`と`.env.*`は`.gitignore`で除外する。
- 安全な設定例だけを`.env.example`としてGit管理する。
- パスワード、Cookie、OAuthトークン、APIキー、秘密鍵、セッション情報を、ソースコード・設定例・テスト結果へ記載しない。
- `git add -f`などで除外を意図的に回避しない。
- 既存の設定例へ実値を貼り付けず、必要な場合は自分の`.env`へ記載する。

新しい種類のローカル設定ファイルを追加する場合は、実値を含むファイルを除外するパターンと、安全な例外ファイルを同時に確認する。

## 設定を追加・変更する場合

次の順序で変更する。

1. その設定を必要とするプロセスと、秘密情報かどうかを決める。
2. 環境変数名を決め、実装と設定例へ追加する。
3. `.env.example`には安全な例だけを追加する。
4. FEまたはBEのローカル開発手順へ、設定の渡し方と確認方法を追加する。
5. クリーンなチェックアウトから、実値をGitへ追加せずに準備できることを確認する。

具体的な外部サービスの認証情報や、実行環境ごとの秘密情報管理は、それを初めて必要とする機能の要求・仕様で決める。
