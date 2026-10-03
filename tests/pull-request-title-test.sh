#!/bin/sh

set -eu

script_path='.github/scripts/validate-pr-title.sh'
test_shell=${BASH:-${SHELL:-sh}}

if [ ! -f "$script_path" ]; then
    printf '失敗: このテストはリポジトリのルートで実行してください。\n' >&2
    exit 1
fi

fail() {
    printf '失敗: %s\n' "$1" >&2
    exit 1
}

expect_valid() {
    test_name=$1
    test_title=$2

    if PR_TITLE=$test_title "$test_shell" "$script_path" >/dev/null 2>&1; then
        printf '成功: %s\n' "$test_name"
    else
        fail "$test_name: 有効なタイトルが拒否されました"
    fi
}

expect_invalid() {
    test_name=$1
    test_title=$2
    test_status=0

    test_output=$(PR_TITLE=$test_title "$test_shell" "$script_path" 2>&1) || test_status=$?
    [ "$test_status" -eq 1 ] || fail "$test_name: 終了コードが1ではありません"
    case "$test_output" in
        '::error::Invalid pull request title format.'*) ;;
        *) fail "$test_name: 形式エラーの案内がありません" ;;
    esac
    printf '成功: %s\n' "$test_name"
}

expect_valid 'Issueタイトルに合わせた形式を受け入れる' \
    'VLM-31 PRタイトル命名規則を定める'
expect_valid '同一Issueへの修正PR形式を受け入れる' \
    'VLM-31 【fix】CI検査の説明を修正'

expect_invalid 'Issue番号の接頭辞がないタイトルを拒否する' \
    'PRタイトル命名規則を定める'
expect_invalid 'Issue番号が数字でないタイトルを拒否する' \
    'VLM-abc PRタイトル命名規則を定める'
expect_invalid 'Issue番号と説明の区切りがないタイトルを拒否する' \
    'VLM-31PRタイトル命名規則を定める'
expect_invalid '説明がないタイトルを拒否する' \
    'VLM-31   '
test_multiline_title=$(printf 'VLM-31 タイトル\n続き')
expect_invalid '複数行のタイトルを拒否する' \
    "$test_multiline_title"

printf 'Pull Requestタイトルのすべてのテストに成功しました。\n'
