#!/bin/bash

NAME=pyaxiom
ORG=axiom-data-science

if [ $# -eq 0 ]; then
    echo "No version specified, exiting"
    exit 1
fi

# Set version to release
sed -i "s/^__version__ = .*/__version__ = \"$1\"/" pyaxiom/__init__.py

# Tag
git tag $1

# Release on PyPi
python setup.py sdist upload

# Push to Git
git push --tags origin master

# Update meta.yml
sed -i "s/version: .*/version: \"$1\"/" conda-recipe/meta.yaml
sed -i "s/git_rev: .*/git_rev: $1/" conda-recipe/meta.yaml

# Build 2.7
conda build -c ioos --python 2.7 conda-recipe
PACKAGE_PATH=`ls ~/miniconda3/conda-bld/**/$NAME*-nppy27*.tar.bz2`
conda convert --platform all $PACKAGE_PATH -o conda-recipe/py27
for f in conda-recipe/py27/**/$NAME*; do
    anaconda upload -u $ORG --force $f
done
rm -r conda-recipe/py27

# Build 3.4
conda build -c ioos --python 3.4 conda-recipe
PACKAGE_PATH=`ls ~/miniconda3/conda-bld/**/$NAME*-nppy34*.tar.bz2`
conda convert --platform all $PACKAGE_PATH -o conda-recipe/py34
for f in conda-recipe/py34/**/$NAME*; do
    anaconda upload -u $ORG --force $f
done
rm -r conda-recipe/py34
