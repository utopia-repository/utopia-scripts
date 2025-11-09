#!/bin/bash
set -xe

rm debian/files -f
git fetch --all
gbp import-orig --uscan
