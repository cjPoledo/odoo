## Overview
- This is an odoo16 project.
- UP Mindanao has an odoo16 based CRM called ISIP (Intelligent Systems for Internal Processes).
- This is not the actual ISIP but just a fork of the odoo16 repo.
- This repo is mainly for developing modules for ISIP.
- The module being developed is in /dev folder.
- Run the instance with: `.venv/bin/python3 odoo-bin -c odoo.conf -d odoo16_dev` (add `-u <module> --dev=all` when developing a module).

## Deployment
- To package a module for deployment, zip it so the module folder itself is the root of the archive (e.g. `upmin_iso.zip` contains `upmin_iso/...` at the top level, not `dev/upmin_iso/...`). `cd` into `/dev` first so the module folder is the top-level entry:
  ```
  cd dev && zip -r ../upmin_iso.zip upmin_iso -x '*__pycache__*' -x '*.pyc' -x '*.DS_Store'
  ```
- Exclude `__pycache__`, `.pyc`, and `.DS_Store` from the archive.
- The resulting zip is placed in the repo root (gitignored) and uploaded directly to the ISIP Odoo instance's Apps > Import Module.

## Rules
- Do not assume. Ask clarifying questions.
- Do not immediately write code. Report first what will be done to achieve the target as concisely as possible and ask for confirmation.
- Use Context7 to reference odoo16 docs.
- Commit everytime important changes are completed. Use conventional commit.
- Inefficient instructions may be given. If there are better alternatives, propose the idea concisely and ask for decision.
- UX is very important. Ensure every update to the code, specially the UI, allows users to have the best experience. Workflows must stay simple and intuitive for non-technical ISIP staff; favor clarity over technical elegance and avoid exposing unnecessary complexity or Odoo internals in the UI.
- Do not scope creep. Only do what is approved. Propose beneficial features that are outside the current scope concisely instead.