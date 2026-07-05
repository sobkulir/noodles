#!/usr/bin/env python3
import os
import sys
import shutil
import argparse
import subprocess

def run_cmd(cmd, check=True, capture_output=False):
    return subprocess.run(cmd, check=check, shell=False, capture_output=capture_output, text=True)

def main():
    parser = argparse.ArgumentParser(description="Deploy script")
    parser.add_argument('-l', '--overwrite-last', action='store_true', help="Overwrite last incremental ID with current deployment")
    parser.add_argument('-n', '--new-index', action='store_true', help="Copy deployment to top-level index.html, js/ and css/")
    args = parser.parse_args()

    # git checkout --quiet main
    run_cmd(['git', 'checkout', '--quiet', 'main'])

    # Check if main has changes
    res = run_cmd(['git', 'diff-index', '--exit-code', '--ignore-submodules', 'HEAD'], check=False, capture_output=True)
    if res.returncode != 0 or res.stdout.strip():
        print("main has some changes, I cannot deploy.", file=sys.stderr)
        sys.exit(1)

    # Get commit ID
    commit_id = run_cmd(['git', 'rev-parse', 'HEAD'], capture_output=True).stdout.strip()[:6]

    # git checkout gh-pages
    run_cmd(['git', 'checkout', 'gh-pages'])
    # git checkout main -- src
    run_cmd(['git', 'checkout', 'main', '--', 'src'])

    # Determine incremental ID
    hist_dir = 'hist'
    os.makedirs(hist_dir, exist_ok=True)
    
    existing_ids = []
    for item in os.listdir(hist_dir):
        if item.isdigit() and os.path.isdir(os.path.join(hist_dir, item)):
            existing_ids.append(int(item))
    
    if existing_ids:
        max_id = max(existing_ids)
    else:
        max_id = 0

    if args.overwrite_last and max_id > 0:
        incremental_id = max_id
    else:
        incremental_id = max_id + 1

    target_dir = os.path.join(hist_dir, str(incremental_id))
    
    if os.path.exists(target_dir):
        shutil.rmtree(target_dir)
    os.makedirs(target_dir, exist_ok=True)

    # cp -r src/* hist/<incremental_ID>
    if os.path.exists('src'):
        for item in os.listdir('src'):
            s = os.path.join('src', item)
            d = os.path.join(target_dir, item)
            if os.path.isdir(s):
                shutil.copytree(s, d)
            else:
                shutil.copy2(s, d)

        # Move to top-level if --new-index is provided
        if args.new_index:
            for d in ['css', 'js', 'index.html']:
                src_path = os.path.join('src', d)
                if os.path.exists(src_path):
                    if os.path.exists(d):
                        if os.path.isdir(d):
                            shutil.rmtree(d)
                        else:
                            os.remove(d)
                    shutil.move(src_path, d)

        # Remove src
        shutil.rmtree('src', ignore_errors=True)

    # Store commit ID in hist/<incremental_ID>/commit_id_<commit_ID>
    commit_file = os.path.join(target_dir, f"commit_id_{commit_id}")
    open(commit_file, 'w').close()

    # touch .nojekyll
    open('.nojekyll', 'w').close()
    
    # date > version.txt
    with open('version.txt', 'w') as f:
        f.write(run_cmd(['date'], capture_output=True).stdout)

    run_cmd(['git', 'add', '-A', '.'])
    run_cmd(['git', 'commit', '-m', f"deploy {commit_id}"], check=False)
    run_cmd(['git', 'push', '-f', 'origin', 'gh-pages'], check=False)

    run_cmd(['git', 'checkout', 'main'])
    run_cmd(['git', 'clean', '-df'])

if __name__ == '__main__':
    main()
