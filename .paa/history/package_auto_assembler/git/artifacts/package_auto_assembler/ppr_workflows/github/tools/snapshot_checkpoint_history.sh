#!/bin/bash

set -euo pipefail

history_root="${1:-.paa/history}"

if [ ! -d "$history_root" ]; then
  exit 0
fi

find "$history_root" -mindepth 1 -maxdepth 1 -type d | while read -r module_dir; do
  worktree_dir="$module_dir/git"
  repo_metadata_dir="$module_dir/git_repo"
  dot_git_dir="$worktree_dir/.git"

  if [ ! -d "$worktree_dir" ] || [ ! -d "$dot_git_dir" ]; then
    continue
  fi

  rm -rf "$repo_metadata_dir"
  cp -R "$dot_git_dir" "$repo_metadata_dir"

  git rm --cached -r "$worktree_dir" >/dev/null 2>&1 || true
  rm -rf "$dot_git_dir"
done
