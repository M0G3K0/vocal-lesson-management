#!/bin/sh

set -eu

hook_path='.githooks/pre-push'
test_old_oid='1111111111111111111111111111111111111111'
test_zero_oid='0000000000000000000000000000000000000000'

if [ ! -f "$hook_path" ]; then
    printf '失敗: このテストはリポジトリのルートで実行してください。\n' >&2
    exit 1
fi

fail() {
    printf '失敗: %s\n' "$1" >&2
    exit 1
}

# Gitがフックとして起動できるよう、実行可能モードで登録されていることを確認する。
test_hook_index_entry=$(git ls-files --stage -- "$hook_path")
case "$test_hook_index_entry" in
    "100755 "*) ;;
    *) fail 'pre-pushフックが実行可能モード（100755）で登録されていません' ;;
esac
printf '成功: pre-pushフックが実行可能モード（100755）で登録されている\n'

# Build valid pre-push input so each test can focus on the branch names.
branch_update() {
    printf 'refs/heads/%s %s refs/heads/%s %s' \
        "$1" "$test_old_oid" "$2" "$test_zero_oid"
}

branch_deletion() {
    printf '(delete) %s refs/heads/%s %s' \
        "$test_zero_oid" "$1" "$test_old_oid"
}

tag_update() {
    printf 'refs/heads/%s %s refs/tags/%s %s' \
        "$1" "$test_old_oid" "$2" "$test_zero_oid"
}

run_hook() {
    test_hook_status=0
    test_hook_output=$(printf '%s\n' "$@" | sh "$hook_path" 2>&1) || test_hook_status=$?
}

warning_for() {
    printf 'WARNING  Invalid branch name format: "%s".\n         See docs/uncategorized/DEVELOPMENT-FLOW.md for the branch naming rules.' "$1"
}

expect_clean() {
    test_name=$1
    shift

    run_hook "$@"
    [ "$test_hook_status" -eq 0 ] || fail "$test_name: フックの終了コードが$test_hook_statusでした"
    [ -z "$test_hook_output" ] || fail "$test_name: 警告なしの想定ですが、次の出力がありました: $test_hook_output"
    printf '成功: %s\n' "$test_name"
}

expect_warning() {
    test_name=$1
    expected_branch=$2
    shift 2

    run_hook "$@"
    [ "$test_hook_status" -eq 0 ] || fail "$test_name: フックの終了コードが$test_hook_statusでした"
    test_expected_output=$(warning_for "$expected_branch")
    [ "$test_hook_output" = "$test_expected_output" ] || fail "$test_name: 警告文が想定と異なります"
    printf '成功: %s\n' "$test_name"
}

expect_branch_warning() {
    test_name=$1
    expected_branch=$2
    local_branch=$3
    remote_branch=$4

    expect_warning "$test_name" "$expected_branch" "$(branch_update "$local_branch" "$remote_branch")"
}

# Valid branch names on the remote are accepted for every allowed type.
expect_clean '6種類のブランチ種別を受け入れる' \
    "$(branch_update source feat/VLM-41-add-search)" \
    "$(branch_update source fix/VLM-42-fix-search)" \
    "$(branch_update source refactor/VLM-43-extract-client)" \
    "$(branch_update source test/VLM-44-test-search)" \
    "$(branch_update source docs/VLM-45-document-rules)" \
    "$(branch_update source chore/VLM-46-update-tools)"

# The destination name is authoritative, even when the local name differs.
expect_branch_warning \
    'ローカル名が正しくても、リモート名が不正なら警告する' \
    'bad/VLM-47-invalid-remote' \
    'feat/VLM-47-valid-local' \
    'bad/VLM-47-invalid-remote'

expect_clean 'ローカル名が不正でも、リモート名が正しければ警告しない' \
    "$(branch_update invalid-local-name chore/VLM-48-valid-remote)"

# main is excepted, while tags and deletions are outside branch naming rules.
expect_clean 'main・タグへのpush・ブランチ削除は対象外にする' \
    "$(branch_update invalid-local-name main)" \
    "$(tag_update invalid-local-name v1)" \
    "$(branch_deletion bad/VLM-49-deleted)"

expect_branch_warning \
    '未対応のブランチ種別を警告する' \
    'build/VLM-50-update-tools' \
    source \
    'build/VLM-50-update-tools'

expect_branch_warning \
    'VLMの記載がない名前を警告する' \
    'chore/50-update-tools' \
    source \
    'chore/50-update-tools'

expect_branch_warning \
    'Issue番号が数字でない名前を警告する' \
    'chore/VLM-x-update-tools' \
    source \
    'chore/VLM-x-update-tools'

expect_branch_warning \
    'Issue番号が0の名前を警告する' \
    'chore/VLM-0-update-tools' \
    source \
    'chore/VLM-0-update-tools'

expect_branch_warning \
    '短い説明が空の名前を警告する' \
    'chore/VLM-51-' \
    source \
    'chore/VLM-51-'

expect_branch_warning \
    '短い説明にスラッシュが含まれる名前を警告する' \
    'chore/VLM-52-update/tools' \
    source \
    'chore/VLM-52-update/tools'

test_expected_output=$(printf '%s\n%s' \
    "$(warning_for 'bad/VLM-53-first')" \
    "$(warning_for 'bad/VLM-54-second')")
run_hook \
    "$(branch_update source bad/VLM-53-first)" \
    "$(branch_update source bad/VLM-54-second)"
[ "$test_hook_status" -eq 0 ] || fail "複数のpush先を確認: フックの終了コードが$test_hook_statusでした"
[ "$test_hook_output" = "$test_expected_output" ] || fail '複数のpush先を確認: 不正な名前ごとに警告が出る想定です'
printf '成功: 複数のpush先を個別に確認する\n'

if [ -c /dev/full ]; then
    test_hook_status=0
    printf '%s\n' "$(branch_update source bad/VLM-55-no-output)" |
        sh "$hook_path" 2>/dev/full || test_hook_status=$?
    [ "$test_hook_status" -eq 0 ] || fail "警告を出力できない場合も続行: フックの終了コードが$test_hook_statusでした"
    printf '成功: 警告を出力できない場合もpushを止めない\n'
else
    printf 'スキップ: /dev/fullがないため、警告出力失敗時の動作は未確認です\n'
fi

printf 'pre-pushフックのすべてのテストに成功しました。\n'
