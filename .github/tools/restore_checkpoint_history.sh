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

  if [ ! -d "$repo_metadata_dir" ]; then
    continue
  fi

  mkdir -p "$worktree_dir"

  if [ -e "$dot_git_dir" ]; then
    continue
  fi

  cp -R "$repo_metadata_dir" "$dot_git_dir"
done
