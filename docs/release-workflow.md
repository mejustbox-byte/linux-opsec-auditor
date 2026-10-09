# Verified release asset publication

The user authorized the full implementation/PR/merge/prerelease cycle. Native uploads
from the cloud task failed with HTTP 401 for uploads.github.com despite working Git/API.
No new credential was requested and no authentication bypass was attempted.

`.github/workflows/release.yml` uses the standard Actions GITHUB_TOKEN instead. It is
manual-only (`workflow_dispatch`) from main with no arbitrary tag/commit inputs.
Hardcoded identity: tag v0.1.0-alpha.1, product commit
70d43abb5bbc5350e7df2ed20e41847bba36938e, existing release ID 407852654.
The workflow never creates a new release and never creates, deletes or updates a tag.

## Trust and permission boundaries

- Build job has contents:read. Reviewed automation is checked out at the dispatch
  commit; product code is checked out at the exact fixed commit. Tag/HEAD checks run
  before executing product code. Build tools are hash-locked; product tests, installed
  CLI smoke and deterministic-wheel checks run on the fixed product tree.
- Checksums and archive inspection compare wheel/source bytes to the fixed Git tree.
  Only wheel, source and SHA256SUMS cross jobs through SHA-pinned Actions artifacts.
- Only the publish job has contents:write. It revalidates transferred bytes, checks
  the exact existing release ID/tag/commit and checks the live remote tag object.
  GH_TOKEN is the standard job-scoped github.token, never a new stored credential.
- Publication puts the same release into draft while updating its three known files.
  `--clobber` permits retrying known file names only; unexpected existing assets cause
  failure. No other release or tag is modified.
- Before publishing, all three files must be uploaded, downloaded back, checksum-
  checked and compared to the fixed source tree. Only then is the same release made
  public as a prerelease. The final public/asset/tag state is checked again.

Dispatch after the separate workflow PR is merged and CI passes:

```bash
gh workflow run release.yml --repo mejustbox-byte/linux-opsec-auditor --ref main
gh run list --repo mejustbox-byte/linux-opsec-auditor --workflow release.yml
```

A successful workflow run and nonempty uploaded assets are required. An empty release,
draft, Git fallback branch or successful build-only job is not completed publication.
A failed upload leaves the same release in draft for safe investigation; rerunning
only touches the expected files and preserves the tag. No paid infrastructure is used.

## Independent verification

```bash
opsec_release_dir=$(mktemp -d)
gh release download v0.1.0-alpha.1 --repo mejustbox-byte/linux-opsec-auditor \
  --dir "$opsec_release_dir" --pattern 'linux_opsec_auditor-0.1.0a1*' --pattern SHA256SUMS
python3 tools/release_artifacts.py verify --directory "$opsec_release_dir" --repo .
```

Fetch the unchanged tag first if the checkout is shallow. The source sdist must contain
exact original tagged files (except the unneeded .gitignore); wheel package files
must equal the tag, with no additional runtime dependencies or unexpected modules.
The helper is release automation, not part of the tagged initial runtime package.
Real platform/LSM/kernel/restore verification remains unexecuted; see laboratory.md.
