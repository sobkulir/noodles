#!/bin/bash

git checkout --quiet main
something_changed=$(git diff-index --exit-code --ignore-submodules HEAD)
if [ -n "$something_changed" ]
then
    echo >&2 "main has some changes, I cannot deploy."
    exit 1
fi

commit_id=$(git show-ref --head | head -c6)
git checkout gh-pages
git checkout main -- src

mkdir -p hist/$commit_id
cp -r src/* hist/$commit_id
mv src/css css
mv src/js js
mv src/index.html index.html
rm -rf src

touch .nojekyll
date > version.txt

git add -A .
git commit -m "deploy $commit_id"
git push -f origin gh-pages

git checkout main
git clean -df