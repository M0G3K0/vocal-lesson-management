#!/bin/sh

set -eu

doc_path='docs/uncategorized/DEVELOPMENT-FLOW.md'
title=${PR_TITLE:-}

invalid_title() {
    printf '::error::Invalid pull request title format. Use "VLM-<Issue number> <title>". See %s.\n' \
        "$doc_path" >&2
    exit 1
}

# GitHubのタイトルは1行とし、Issue番号の形式と説明の有無だけを確認する。
case "$title" in
    *'
'*) invalid_title ;;
esac

case "$title" in
    VLM-*) remainder=${title#VLM-} ;;
    *) invalid_title ;;
esac

case "$remainder" in
    *' '*) issue_number=${remainder%% *}; description=${remainder#* } ;;
    *) invalid_title ;;
esac

case "$issue_number" in
    ''|*[!0-9]*) invalid_title ;;
esac

case "$description" in
    *[![:space:]]*) ;;
    *) invalid_title ;;
esac
