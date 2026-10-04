---
last_updated: "2026-10-05"
---

# フロントエンドのローカル開発環境

この文書は、GitHub Issue [#48](https://github.com/M0G3K0/vocal-lesson-management/issues/48)で構築したフロントエンドのローカル開発環境と、その再現手順を記録する。

## 構成

フロントエンドは、`frontend/`以下のAngularアプリケーションとして構成する。

```
frontend/
├── src/
│   ├── app/       Angularアプリケーションのコード
│   ├── assets/    ビルド後に配信する静的アセット
│   └── ...
├── angular.json   ビルド・開発サーバー・テストの設定
├── package.json   パッケージと実行スクリプトの定義
├── pnpm-lock.yaml 依存関係の解決結果
├── pnpm-workspace.yaml pnpmのビルドスクリプト許可設定
└── .node-version  使用するNode.jsのバージョン
```

アプリケーション内部の配置と責務は、[フロントエンドのアプリケーションアーキテクチャ](./FRONTEND-ARCHITECTURE.md)に従う。

ローカル設定と秘密情報の共通ルールは、[ローカル設定と秘密情報の扱い](./LOCAL-CONFIGURATION.md)に従う。

## 採用バージョン

| 対象 | バージョン・条件 |
| --- | --- |
| Angular・Angular CLI | 22.2系 |
| TypeScript | 6.0系 |
| Node.js | 24.15.0以上、25未満 |
| pnpm | 12.8.2 |
| Vitest | Angular CLIが選択する5系 |

Node.jsの条件は、Angular 22.2系の互換条件を満たすために設定する。

リポジトリ内では、次の設定で使用するNode.jsとpnpmを確認できる。

- `frontend/.node-version`
- `frontend/package.json`の`engines`
- `frontend/package.json`の`packageManager`

依存パッケージの具体的な解決結果は、`frontend/pnpm-lock.yaml`を正とする。

## 前提

次のツールをローカルに用意する。

- Node.js 24.15.0以上、25未満
- pnpm 12.8.2

Angular CLIとVitestは、`frontend/package.json`の依存関係として使用する。グローバルにAngular CLIをインストールする必要はない。

## 初回セットアップ

リポジトリのルートで実行する。

### バージョンを確認する

```
node --version
pnpm --version
```

Node.jsは`v24.15.0`以上、pnpmは`12.8.2`であることを確認する。

### パッケージをインストールする

```
pnpm --dir frontend install --frozen-lockfile
```

`--frozen-lockfile`を指定し、`pnpm-lock.yaml`を変更せずに依存関係をインストールする。

## VS Codeから起動する

リポジトリのルートをVS Codeで開く。

実行とデバッグから`Frontend: ng serve`を選ぶと、次の処理が実行される。

- `frontend/`を対象に開発サーバーを起動する
- `http://127.0.0.1:4200/`をブラウザで開く

VS Codeの設定はリポジトリルートの`.vscode/`に置く。

## コマンドラインから起動する

リポジトリルートで、次のコマンドを実行する。

```text
pnpm --dir frontend run start --host 127.0.0.1 --port 4200
```

`ng serve`をリポジトリルートで直接実行せず、`frontend/`を対象に実行する。

## 開発サーバーを起動する

```
pnpm --dir frontend run start --host 127.0.0.1 --port 4200
```

ブラウザで`http://localhost:4200/`を開き、Angularアプリケーションが表示されることを確認する。

終了するときは、開発サーバーを起動したターミナルで`Ctrl+C`を入力する。

## ビルドする

```
pnpm --dir frontend run build
```

ビルド成果物は`frontend/dist/frontend/`以下に出力される。`dist/`はビルド生成物として扱い、Gitには追加しない。

## テストを実行する

```
pnpm --dir frontend run test
```

Vitestが非ウォッチモードで実行され、初期テストが成功することを確認する。

## 静的アセットを確認する

静的アセットは`frontend/src/assets/`に置く。

`frontend/angular.json`の設定により、`src/assets/`以下のファイルはビルド後の`assets/`へコピーされる。

初期状態では、`src/assets/favicon.ico`を`assets/favicon.ico`として配信する。

ビルド後に、次のファイルが存在することを確認する。

```
frontend/dist/frontend/browser/assets/favicon.ico
```

新しい画像やアイコンなどを追加するときは、`src/app/`ではなく`src/assets/`以下へ置く。

## クリーンなチェックアウトからの再現

クリーンなチェックアウトでは、次の順序で実行する。

1. Node.jsとpnpmのバージョンを確認する。
2. `pnpm --dir frontend install --frozen-lockfile`を実行する。
3. `pnpm --dir frontend run build`を実行する。
4. `pnpm --dir frontend run test`を実行する。
5. 必要に応じて`pnpm --dir frontend run start`で開発サーバーを起動する。

この手順で、依存関係のインストール、ビルド、テスト、開発サーバーの起動を再現できる。

現在、フロントエンドへ渡すローカル設定はない。設定が追加された場合は、[ローカル設定と秘密情報の扱い](./LOCAL-CONFIGURATION.md)を参照し、ブラウザへ公開してよい値だけをプロセスへ渡す。
