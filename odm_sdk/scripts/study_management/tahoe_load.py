#!/usr/bin/env python3
"""
Create a Tahoe-100M study + samples + libraries + 14 plate attachments on an
ODM instance, then optionally queue the per-plate h5ad transformation jobs.

Stages:
  1. POST import/study/        (sync, fast: TSV ingest)      -> study accession
  2. POST import/samples/      (sync, fast: TSV ingest)      -> samples linked
  3. POST import/libraries/    (sync, fast: TSV ingest)      -> libraries linked
  4. POST import/file/         (one per plate, parallel)     -> 14 file jobs
  5. POST transformations/jobs (one per attached h5ad)       -> 14 transform jobs

Step 5 is opt-in via `--transform`. Each transformation runs `hdf5-cells`
against one of the imported h5ad attachments (its accession from step 4)
under a pre-existing transformation configuration. The transformation jobs
are fire-and-forget — they get queued server-side and run on their own pace.

By default the script returns once all file-import jobs have been *submitted*.
Pass `--watch` to also poll those jobs to completion (needed to learn each
attachment's accession, which the transformation step needs).

A manifest at ./tahoe_manifest.json records all the accessions and job ids so
the script is resumable: `--watch-only`, `--files-only`, `--transform-only`,
`--ensure-links`, `--add-libraries` all read it.

Required per-run:
  --server          ODM base URL (e.g. https://<instance>.example.com)
  --token           API token, or set GENESTACK_API_TOKEN env var
  --template        per-instance template accession applied to study/samples/libraries
  --transform-config-id   per-instance transformation configuration_id (only when --transform)

Unattended/background running — the script blocks for hours under --watch.
Just run it under `nohup` (or `screen`/`tmux`) and tail the log:

    export GENESTACK_API_TOKEN=...
    nohup python tahoe_load.py --server $SERVER --template $TMPL \
        --transform --transform-config-id $CFG --watch \
        > tahoe_load.log 2>&1 &
    tail -f tahoe_load.log

Or, do the steps in chunks to control babysitting more tightly:

    # 1. Submit file imports, return immediately (writes manifest):
    python tahoe_load.py --server $SERVER --template $TMPL
    # 2. Later, poll until file imports complete:
    python tahoe_load.py --server $SERVER --template $TMPL --watch-only
    # 3. Once accessions are known, queue transformations:
    python tahoe_load.py --server $SERVER --template $TMPL \
        --transform-only --transform-config-id $CFG
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from pathlib import Path

import requests

sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# --server and --token must be provided per-run. Server URL and API token are
# instance-specific — never bake them in. Token comes from --token or the
# GENESTACK_API_TOKEN env var.
DEFAULT_TOKEN = os.environ.get("GENESTACK_API_TOKEN")

# Public Tahoe-100M demo data — same on any ODM instance.
DEFAULT_STUDY_TSV = "https://bio-test-data.s3.us-east-1.amazonaws.com/demo_materials/onco/Tahoe/study.tsv"
DEFAULT_SAMPLES_TSV = "https://bio-test-data.s3.us-east-1.amazonaws.com/demo_materials/onco/Tahoe/samples.tsv"
DEFAULT_LIBRARIES_TSV = "https://bio-test-data.s3.us-east-1.amazonaws.com/demo_materials/onco/Tahoe/libraries.tsv"
DEFAULT_DATA_CLASS = "Single-cell transcriptomics"
DEFAULT_PARALLELISM = 4

# Transformation image defaults — platform-level, same across instances. The
# `configuration_id` is server-side state with a per-instance ID; pass it
# explicitly with --transform-config-id. The `--template` accession is also
# per-instance state with no portable default.
DEFAULT_TRANSFORM_IMAGE_NAME = "hdf5-cells"
DEFAULT_TRANSFORM_IMAGE_VERSION = "1.0.0-24"
DEFAULT_TRANSFORM_MEMORY = "35Gi"
DEFAULT_TRANSFORM_VOLUME = "35Gi"

PLATES = [
    f"plate{n}_filt_Vevo_Tahoe100M_WServicesFrom_ParseGigalab" for n in range(1, 15)
]
H5AD_BASE = "https://storage.googleapis.com/arc-institute-virtual-cell-atlas/tahoe100M/2025-02-25/h5ad"
META_BASE = "https://bio-test-data.s3.us-east-1.amazonaws.com/demo_materials/onco/Tahoe/data_metadata"
PLATE_FILES = [
    {
        "plate": p,
        "data": f"{H5AD_BASE}/{p}.h5ad",
        "metadata": f"{META_BASE}/{p}_metadata.tsv",
    }
    for p in PLATES
]

URL_PREFIX = "api/v1/jobs"
LINK_PREFIX = "api/v1/as-curator/integration/link"
TRANSFORM_PREFIX = "api/v1/transformations/jobs"
RUNNING_STATUSES = {"STARTING", "STARTED", "RUNNING"}
TERMINAL_STATUSES = {"COMPLETED", "FAILED", "CANCELLED"}


@dataclass
class FileJob:
    plate: str
    data_link: str
    metadata_link: str
    job_exec_id: int | None = None
    status: str | None = None
    accession: str | None = None
    error: str | None = None


@dataclass
class TransformationJob:
    """One transformation queued against one imported attachment.

    Mirrors the Processors Controller `TransformationJobFields` schema for the
    fields we care about. See `api/oas/openapi.yaml` (or the live Swagger at
    /swagger/?urls.primaryName=processorsController) for the full surface.

    State lifecycle (from `TransformationState` enum):
      PENDING | WAITING | RUNNING -> DONE | FAILED  (UNKNOWN can appear anywhere)
    Terminal states for polling: DONE, FAILED.
    """
    plate: str
    input_accession: str          # the h5ad attachment accession (FileJob.accession)
    config_id: int
    image_name: str
    image_version: str
    memory_size: str
    volume_size: str
    job_id: int | None = None         # `id` field of the POST response (int64 per spec)
    submit_status: str | None = None  # "SUBMITTED" | "SUBMIT_FAILED" (script-side tracking)
    state: str | None = None          # server-side state — TransformationState enum value
    state_reason: str | None = None   # e.g. "OOMKilled" when state=FAILED
    state_description: str | None = None
    create_time: str | None = None
    end_time: str | None = None
    error: str | None = None


@dataclass
class Manifest:
    server: str
    template_id: str
    study_accession: str | None = None
    samples_group_accession: str | None = None
    libraries_group_accession: str | None = None
    file_jobs: list[FileJob] = field(default_factory=list)
    transformation_jobs: list[TransformationJob] = field(default_factory=list)


# ---------------------------------------------------------------------------
# HTTP plumbing
# ---------------------------------------------------------------------------


def _headers(token: str) -> dict:
    return {
        "Genestack-API-Token": token,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def _post_import(server: str, token: str, kind: str, payload: dict, allow_dups: bool = False) -> int:
    """Submit an import job. Returns jobExecId."""
    print(f"[submit] import/{kind} with payload: {payload}")
    qs = "?allow_dups=true" if (allow_dups and kind != "file") else ""
    url = f"{server}/{URL_PREFIX}/import/{kind}{qs}"
    print(f"[submit] POST {url} ...")
    r = requests.post(url, headers=_headers(token), json=payload, timeout=60)
    if r.status_code != 200:
        raise RuntimeError(f"POST import/{kind} failed ({r.status_code}): {r.text[:500]}")
    body = r.json()
    job_id = body.get("jobExecId")
    if job_id is None:
        raise RuntimeError(f"POST import/{kind} returned no jobExecId: {body}")
    return int(job_id)


def _job_status(server: str, token: str, job_id: int) -> str:
    url = f"{server}/{URL_PREFIX}/{job_id}/info"
    r = requests.get(url, headers=_headers(token), timeout=30)
    r.raise_for_status()
    return r.json().get("status", "UNKNOWN")


def _job_output(server: str, token: str, job_id: int) -> dict:
    url = f"{server}/{URL_PREFIX}/{job_id}/output"
    r = requests.get(url, headers=_headers(token), timeout=30)
    r.raise_for_status()
    return r.json()


def _post_link(server: str, token: str, path: str) -> int:
    """POST an integration-link endpoint. Returns the HTTP status.

    `path` is the bit after `/api/v1/as-curator/integration/link/`,
    e.g. `sample/group/{sourceId}/to/study/{targetId}` already substituted.

    Backend semantics observed (from
    unified/.../link/<X>GroupTo<Y>.java + SignalLinkingFacade): 204 = link
    created, 200 = partially linked (signal/cell groups; not relevant here),
    409 = link already exists, 4xx else = real error. We treat 200/204/409
    as success so the call is idempotent.
    """
    url = f"{server}/{LINK_PREFIX}/{path}"
    print(f"[link] POST {url}")
    # Link calls can be slow on large groups: linking ~67k library rows to
    # samples takes well over a minute on dev. The server completes even if
    # the client gives up, but we lose the response and the in-memory state
    # — bump to 5 minutes so we actually capture the success.
    r = requests.post(url, headers=_headers(token), timeout=1800)
    if r.status_code in (200, 204):
        return r.status_code
    if r.status_code == 409:
        # Already linked; treat as success for idempotency.
        print(f"[link] {path} already exists (409); skipping.")
        return r.status_code
    raise RuntimeError(f"POST link/{path} failed ({r.status_code}): {r.text[:500]}")


def _link_sample_group_to_study(server: str, token: str,
                                 sample_group_accession: str,
                                 study_accession: str) -> None:
    _post_link(
        server, token,
        f"sample/group/{sample_group_accession}/to/study/{study_accession}"
    )


def _link_library_group_to_sample_group(server: str, token: str,
                                         library_group_accession: str,
                                         sample_group_accession: str) -> None:
    _post_link(
        server, token,
        f"library/group/{library_group_accession}/to/sample/group/{sample_group_accession}"
    )


def _link_cell_group_to_library_group(server: str, token: str,
                                       cell_group_accession: str,
                                       library_group_accession: str) -> None:
    """Cell-group → library-group SLP link. Mirrors the link the hdf5-cells
    transformation pod issues internally after uploading cells."""
    _post_link(
        server, token,
        f"cell/group/{cell_group_accession}/to/library/group/{library_group_accession}"
    )


def _list_cell_groups_in_study(server: str, token: str, study_accession: str) -> list[dict]:
    """List cell groups attached to a study, surfacing all system metainfo so
    `genestack:transformationSourceAttachmentAccession` is visible. Mirrors
    the path that the hdf5-cells transformation pod uses internally
    (`_list_groups_by_study` in transformation-images/hdf5-cells/lib/api_wrappers.py).

    Endpoint: GET /api/v1/as-curator/integration/link/cell/group/by/study/{study}
    with `?returnedMetadataFields=all` so the response carries the system
    metainfo we need to match against the source attachment.

    Returns the list of `{itemId, metadata}` dicts. Empty list if the study
    has no cell groups.
    """
    url = (
        f"{server}/{LINK_PREFIX}/cell/group/by/study/{study_accession}"
        f"?returnedMetadataFields=all"
    )
    r = requests.get(url, headers=_headers(token), timeout=120)
    r.raise_for_status()
    body = r.json()
    return body if isinstance(body, list) else []


def _find_cell_group_for_source_attachment(
    cell_groups: list[dict], source_attachment_accession: str
) -> str | None:
    """Among the cell groups returned by `_list_cell_groups_in_study`, find the
    one whose `genestack:transformationSourceAttachmentAccession` references
    the given source attachment. Returns the accession or None.

    Matches the transformation pod's `find_existing_group_for_source_attachment`
    logic so an --ensure-links run heals exactly the cell groups that an in-pod
    reuse-lookup would find.
    """
    key = "genestack:transformationSourceAttachmentAccession"
    for item in cell_groups:
        metadata = item.get("metadata") or {}
        ref = metadata.get(key)
        # The ref can come back as a string accession or a FileReference dict.
        if isinstance(ref, dict):
            ref = ref.get("accession") or ref.get("genestack:accession")
        if ref == source_attachment_accession:
            return item.get("itemId") or metadata.get("genestack:accession")
    return None


def _wait_for_job(server: str, token: str, job_id: int, label: str, poll_s: int = 5,
                  timeout_s: int | None = None) -> dict:
    """Block until a job leaves STARTING/STARTED/RUNNING. Returns its final output."""
    started = time.time()
    while True:
        status = _job_status(server, token, job_id)
        if status not in RUNNING_STATUSES:
            break
        if timeout_s is not None and (time.time() - started) > timeout_s:
            raise TimeoutError(
                f"{label} (jobExecId={job_id}) still {status} after {timeout_s}s"
            )
        time.sleep(poll_s)
    output = _job_output(server, token, job_id)
    final_status = output.get("status", status)
    if final_status != "COMPLETED":
        raise RuntimeError(
            f"{label} (jobExecId={job_id}) ended {final_status}: "
            f"{output.get('errors') or output.get('result') or output}"
        )
    return output


# ---------------------------------------------------------------------------
# Stages
# ---------------------------------------------------------------------------


def submit_study(server: str, token: str, study_tsv: str, template: str | None) -> str:
    """Create the study. Blocks until the study TSV ingest finishes — fast."""
    payload: dict = {"metadataLink": study_tsv, "dataSource": "S3"}
    if template:
        payload["templateId"] = template
    print(f"[study] submitting {study_tsv} ...")
    job_id = _post_import(server, token, "study", payload, allow_dups=True)
    output = _wait_for_job(server, token, job_id, "study import")
    accession = output.get("result", {}).get("accession")
    if not accession:
        raise RuntimeError(f"study import returned no accession: {output}")
    print(f"[study] created {accession}")
    return accession


def submit_samples(server: str, token: str, samples_tsv: str, study_accession: str,
                   template: str | None) -> str:
    """Import samples and link the resulting sample group to the study.

    Two backend calls: (1) POST import/samples returns an
    ImportMetadataGroupJobResult with `groupAccession`. The endpoint does
    NOT accept studyAccession in the JSON body (ImportMetadataRequest has
    no such field), so the import doesn't link to the study by itself.
    (2) POST integration/link/sample/group/{group}/to/study/{study} creates
    the link — this is the missing step that's hiding samples in the GUI
    if you only call (1).
    """
    payload: dict = {
        "metadataLink": samples_tsv,
        "dataSource": "S3",
    }
    if template:
        payload["templateId"] = template
    print(f"[samples] submitting {samples_tsv} ...")
    job_id = _post_import(server, token, "samples", payload, allow_dups=True)
    output = _wait_for_job(server, token, job_id, "samples import")
    group_accession = (output.get("result") or {}).get("groupAccession")
    if not group_accession:
        raise RuntimeError(f"samples import returned no groupAccession: {output}")
    print(f"[samples] created group {group_accession}; linking to study {study_accession}")
    _link_sample_group_to_study(server, token, group_accession, study_accession)
    return group_accession


def submit_libraries(server: str, token: str, libraries_tsv: str,
                     sample_group_accession: str, template: str | None) -> str:
    """Import libraries and link the library group to the sample group.

    Mirrors submit_samples: import returns groupAccession, then a
    separate POST establishes the library-group → sample-group link.
    Libraries don't link to studies directly — they hang off the sample
    group which itself links to the study.
    """
    payload: dict = {
        "metadataLink": libraries_tsv,
        "dataSource": "S3",
    }
    if template:
        payload["templateId"] = template
    print(f"[libraries] submitting {libraries_tsv} ...")
    job_id = _post_import(server, token, "libraries", payload, allow_dups=True)
    output = _wait_for_job(server, token, job_id, "libraries import")
    group_accession = (output.get("result") or {}).get("groupAccession")
    if not group_accession:
        raise RuntimeError(f"libraries import returned no groupAccession: {output}")
    print(f"[libraries] created group {group_accession}; "
          f"linking to sample group {sample_group_accession}")
    _link_library_group_to_sample_group(
        server, token, group_accession, sample_group_accession
    )
    return group_accession


def ensure_links(server: str, token: str, manifest: Manifest) -> None:
    """Re-establish any missing links among the entities recorded in the
    manifest. Idempotent — uses _post_link which treats 409 (already
    linked) as success. Run this after a partial-failure import or when
    samples/libraries don't show up in the GUI because the link step was
    missed by an older version of the script.

    Covers three link types:
      1. sample group → study
      2. library group → sample group
      3. cell group → library group (NEW)

    The first two are entity links created at study-load time. The third is
    normally created by the hdf5-cells transformation pod after a successful
    cell-metadata upload — but failure modes between cell upload and SLP
    linking (e.g. distributed DDL queue timeouts on the temp-table CREATE
    inside findExistingSLPCellLinks) can leave a cell group fully uploaded
    but unlinked. --ensure-links discovers those cell groups via the
    standard `link/cell/group/by/study/{study}` endpoint and links each one
    to the manifest's library group.

    WARNING: linking heals "uploaded but unlinked" cell groups, but NOT
    "uploaded partially then crashed" cell groups. The pod's cell uploader
    flushes in 50,000-row chunks; an interrupted upload leaves a row count
    that is an exact multiple of 50,000. Re-linking such a group would
    fully linkify an incomplete dataset and let downstream transformations
    propagate the missing cells. ensure_links warns when it sees a suspect
    row count (matching pattern), but it cannot inspect the source h5ad
    to verify the expected count — callers seeing the warning should
    delete the suspect cell group and re-run the transformation instead.

    Doesn't touch file_jobs — the file→study link is handled by the
    importExpression flow itself when each plate's job completes (each
    file gets attached as a study AFile via studyAccession in the import
    payload).
    """
    if manifest.samples_group_accession and manifest.study_accession:
        print(f"[ensure-links] sample group {manifest.samples_group_accession} → "
              f"study {manifest.study_accession}")
        _link_sample_group_to_study(
            server, token,
            manifest.samples_group_accession,
            manifest.study_accession,
        )
    if manifest.libraries_group_accession and manifest.samples_group_accession:
        print(f"[ensure-links] library group {manifest.libraries_group_accession} → "
              f"sample group {manifest.samples_group_accession}")
        _link_library_group_to_sample_group(
            server, token,
            manifest.libraries_group_accession,
            manifest.samples_group_accession,
        )
    if not manifest.samples_group_accession:
        print("[ensure-links] no samples_group_accession in manifest; skipping.")
    ensure_cell_links(server, token, manifest)


def ensure_cell_links(server: str, token: str, manifest: Manifest) -> None:
    """Find cell groups in the study created by hdf5-cells transformations and
    link any that are missing the library-group SLP link. Idempotent.

    Cross-references manifest.file_jobs accessions (each = a source attachment
    fed into a transformation) against the study's cell groups; only links
    cell groups whose `genestack:transformationSourceAttachmentAccession`
    matches one of the loaded plates. Cell groups produced by an unrelated
    workflow on the same study are left alone.

    Skipped when the manifest is missing study or library group accessions
    (nothing to link to).
    """
    if not manifest.study_accession or not manifest.libraries_group_accession:
        print("[ensure-links] cell-group linking skipped: "
              "missing study_accession or libraries_group_accession in manifest.")
        return

    source_accs = {fj.accession for fj in manifest.file_jobs if fj.accession}
    if not source_accs:
        print("[ensure-links] cell-group linking skipped: "
              "no file_jobs with accessions in manifest.")
        return

    try:
        cell_groups = _list_cell_groups_in_study(server, token, manifest.study_accession)
    except Exception as exc:
        print(f"[ensure-links] failed to list cell groups in study "
              f"{manifest.study_accession}: {exc}")
        return

    print(f"[ensure-links] checking {len(cell_groups)} cell group(s) in study "
          f"{manifest.study_accession} against {len(source_accs)} loaded source attachment(s)")
    linked = 0
    skipped = 0
    for src_acc in sorted(source_accs):
        cg_acc = _find_cell_group_for_source_attachment(cell_groups, src_acc)
        if not cg_acc:
            continue
        print(f"[ensure-links] cell group {cg_acc} (source={src_acc}) → "
              f"library {manifest.libraries_group_accession}")
        try:
            _link_cell_group_to_library_group(
                server, token, cg_acc, manifest.libraries_group_accession
            )
            linked += 1
        except Exception as exc:
            # 409 is already handled inside _post_link; anything else here
            # is a real failure. Don't abort the whole pass — log and move on.
            print(f"[ensure-links] cell group {cg_acc} link failed: {exc}")
            skipped += 1
    print(f"[ensure-links] cell-group linking: {linked} linked (or already linked), "
          f"{skipped} failed.")


def submit_file(server: str, token: str, study_accession: str, plate: dict,
                data_class: str) -> FileJob:
    """Fire-and-forget: submit a single file import job, return the FileJob."""
    fj = FileJob(plate=plate["plate"], data_link=plate["data"],
                 metadata_link=plate["metadata"])
    payload = {
        "dataLink": fj.data_link,
        "metadataLink": fj.metadata_link,
        "dataClass": data_class,
        "studyAccession": study_accession,
        "dataSource": "HTTP",
    }
    try:
        fj.job_exec_id = _post_import(server, token, "file", payload, allow_dups=True)
        # Backend state is whatever it is — STARTING right after submit. Don't
        # bake an optimistic "RUNNING" into the manifest because watch_jobs
        # would then log a confusing "RUNNING -> STARTING" transition on first
        # poll and stay silent for jobs that genuinely are RUNNING.
        fj.status = "STARTING"
        print(f"[file] {fj.plate}: jobExecId={fj.job_exec_id}")
    except Exception as exc:
        fj.error = str(exc)
        fj.status = "SUBMIT_FAILED"
        print(f"[file] {fj.plate}: SUBMIT FAILED — {exc}")
    return fj


def submit_all_files(server: str, token: str, study_accession: str,
                     plates: list[dict], parallelism: int,
                     data_class: str) -> list[FileJob]:
    """Submit every plate's import in parallel (bounded). Each call is one
    HTTP POST and returns immediately with a jobExecId; the actual
    rclone copy + AFile registration happens server-side."""
    jobs: list[FileJob] = []
    with ThreadPoolExecutor(max_workers=parallelism) as ex:
        futures = [
            ex.submit(submit_file, server, token, study_accession, p, data_class)
            for p in plates
        ]
        for fut in as_completed(futures):
            jobs.append(fut.result())
    # preserve plate order in the manifest
    plate_order = {p["plate"]: i for i, p in enumerate(plates)}
    jobs.sort(key=lambda j: plate_order.get(j.plate, 1_000_000))
    return jobs


# ---------------------------------------------------------------------------
# Transformation submission
# ---------------------------------------------------------------------------


def _transform_headers(token: str) -> dict:
    """Headers for Processors Controller endpoints.

    Per `api/oas/openapi.yaml`, POST /api/v1/transformations/jobs requires the
    `Ad-Hoc-Genestack-API-Token` header. Empirically the gateway also accepts
    the regular `Genestack-API-Token`, but the spec is authoritative — send
    both so the request works regardless of which one the controller's
    middleware looks at.
    """
    return {
        "Genestack-API-Token": token,
        "Ad-Hoc-Genestack-API-Token": token,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def _post_transformation(
    server: str, token: str, accession: str,
    config_id: int, image_name: str, image_version: str,
    memory: str, volume: str,
) -> int:
    """POST one transformation job. Returns the job id (int64 per spec).

    Endpoint: POST /api/v1/transformations/jobs
    Body shape: `TransformationJobCreateFields` schema.
    Response 200: `TransformationJobId` = `{ "id": <int64> }`.
    """
    url = f"{server}/{TRANSFORM_PREFIX}"
    payload = {
        "configuration_id": config_id,
        "dry_run": False,
        "image_reference": {"name": image_name, "version": image_version},
        "input_accessions": [accession],
        "memory_size": memory,
        "volume_size": volume,
    }
    print(f"[transform] POST {url}  input={accession} image={image_name}:{image_version}")
    # 5-minute timeout: the controller's POST /transformations/jobs is synchronous
    # over the k8s job-creation path and can take >60s under load (observed
    # 2026-05-11 — 14 concurrent POSTs all timed out client-side at 60s while
    # the server actually accepted and queued every transformation). Pair with
    # the server-state reconciliation in submit_transformations() to recover
    # phantom-failure manifest entries from any older runs.
    r = requests.post(url, headers=_transform_headers(token), json=payload, timeout=300)
    if r.status_code not in (200, 201, 202):
        raise RuntimeError(
            f"POST transformations/jobs failed ({r.status_code}) for {accession}: {r.text[:500]}"
        )
    body = r.json() if r.text else {}
    job_id = body.get("id")
    if job_id is None:
        # Fall back to a permissive lookup in case the response shape ever
        # drifts (the spec is marked "beta"). Surface the full body so the
        # caller can decide.
        for key in ("jobId", "job_id", "transformation_job_id", "transformationId"):
            if body.get(key) is not None:
                job_id = body[key]
                break
    if job_id is None:
        raise RuntimeError(f"POST transformations/jobs returned no id field: {body}")
    return int(job_id)


def _get_transformation(server: str, token: str, job_id: int) -> dict:
    """GET /api/v1/transformations/jobs/{id} — returns TransformationJobFields.

    Used for polling. Status lives under `status.state` (one of
    PENDING/WAITING/RUNNING/DONE/FAILED/UNKNOWN); `status.reason` is set on
    failure (e.g. "OOMKilled") and `status.description` is a human-readable
    note when present.
    """
    url = f"{server}/{TRANSFORM_PREFIX}/{job_id}"
    r = requests.get(url, headers=_transform_headers(token), timeout=30)
    r.raise_for_status()
    return r.json()


def _list_transformations(server: str, token: str) -> list[dict]:
    """GET /api/v1/transformations/jobs — returns array of TransformationJob.

    Used by submit_transformations to reconcile against server state before
    POSTing. The list endpoint isn't paginated in the OpenAPI spec, so it
    returns ALL historical jobs — match by input_accession (which is unique
    per attachment) to find our recent ones.
    """
    url = f"{server}/{TRANSFORM_PREFIX}"
    r = requests.get(url, headers=_transform_headers(token), timeout=60)
    r.raise_for_status()
    body = r.json()
    return body if isinstance(body, list) else []


def _reconcile_from_server(
    existing: list[TransformationJob],
    file_jobs: list[FileJob],
    server_jobs: list[dict],
    config_id: int, image_name: str, image_version: str,
    memory: str, volume: str,
) -> tuple[list[TransformationJob], set[str]]:
    """Cross-reference server-side transformation jobs against the manifest.

    For each file_job with COMPLETED status + accession, look for the most
    recent server-side transformation whose input_accessions contains that
    accession. If found:
      - rescue any SUBMIT_FAILED manifest entry into SUBMITTED with the real id
      - create a fresh manifest entry if none existed
      - refresh state fields (state, state_reason, ...) from the server

    Returns (updated_manifest_entries, accessions_with_server_state).
    Callers use the second set to skip POSTing for those accessions.
    """
    # Build map: input_accession → most recent server job.
    server_by_acc: dict[str, dict] = {}
    for sj in server_jobs:
        for acc in (sj.get("input_accessions") or []):
            prev = server_by_acc.get(acc)
            # create_time is ISO 8601 → lexicographically orderable
            if prev is None or (sj.get("create_time", "") > prev.get("create_time", "")):
                server_by_acc[acc] = sj

    by_input = {t.input_accession: t for t in existing if t.input_accession}
    file_acc_to_plate = {fj.accession: fj.plate for fj in file_jobs if fj.accession}

    reconciled_accs: set[str] = set()
    rescued = 0
    discovered = 0
    for acc, plate in file_acc_to_plate.items():
        sj = server_by_acc.get(acc)
        if not sj:
            continue
        reconciled_accs.add(acc)
        sj_id = int(sj["id"]) if sj.get("id") is not None else None
        status = sj.get("status") or {}
        sj_state = status.get("state")
        sj_reason = status.get("reason")
        sj_desc = status.get("description")
        sj_create = sj.get("create_time")
        sj_end = sj.get("end_time")

        t = by_input.get(acc)
        if t is None:
            # No manifest entry at all — invent one from server state.
            new_t = TransformationJob(
                plate=plate, input_accession=acc,
                config_id=int(sj.get("configuration_id") or config_id),
                image_name=(sj.get("image_reference") or {}).get("name") or image_name,
                image_version=(sj.get("image_reference") or {}).get("version") or image_version,
                memory_size=sj.get("memory_size") or memory,
                volume_size=sj.get("volume_size") or volume,
                job_id=sj_id,
                submit_status="SUBMITTED",
                state=sj_state, state_reason=sj_reason, state_description=sj_desc,
                create_time=sj_create, end_time=sj_end,
            )
            existing.append(new_t)
            by_input[acc] = new_t
            discovered += 1
            print(f"[reconcile] {plate}: discovered server-side job id={sj_id} state={sj_state}")
        elif t.submit_status != "SUBMITTED" or t.job_id is None:
            # Manifest says SUBMIT_FAILED (or has no id) — rescue from server.
            t.job_id = sj_id
            t.submit_status = "SUBMITTED"
            t.error = None
            t.state = sj_state
            t.state_reason = sj_reason
            t.state_description = sj_desc
            t.create_time = sj_create
            t.end_time = sj_end
            rescued += 1
            print(f"[reconcile] {plate}: rescued SUBMIT_FAILED → SUBMITTED id={sj_id} state={sj_state}")
        else:
            # Manifest already has SUBMITTED with an id — just refresh state.
            t.state = sj_state or t.state
            t.state_reason = sj_reason
            t.state_description = sj_desc
            if sj_create:
                t.create_time = sj_create
            if sj_end:
                t.end_time = sj_end

    if discovered:
        print(f"[reconcile] discovered {discovered} new transformation(s) from server state")
    if rescued:
        print(f"[reconcile] rescued {rescued} SUBMIT_FAILED entry/entries from server state")
    return existing, reconciled_accs


def submit_transformations(
    server: str, token: str, file_jobs: list[FileJob],
    existing: list[TransformationJob],
    config_id: int, image_name: str, image_version: str,
    memory: str, volume: str,
    parallelism: int = 4,
    no_submit: bool = False,
    auto_confirm: bool = False,
    skip_plates: frozenset[str] = frozenset(),
) -> list[TransformationJob]:
    """Queue one transformation per completed h5ad attachment.

    Idempotent: skips file_jobs whose accession already has a non-failed
    TransformationJob in `existing`. Returns the FULL (existing + new) list
    so the caller can write it back to the manifest.

    Each transformation is fire-and-forget — the script doesn't poll their
    status. Look in the ODM Task Manager GUI / /api/v1/transformations/jobs/{id}
    for progress.

    Self-healing: before any POST, list server-side transformations and match
    by input_accession. If the server already has a transformation for one of
    our file accessions, record/refresh it in the manifest and skip the POST.
    This recovers from earlier client-side timeouts where the server actually
    accepted the request but the script marked the manifest entry as
    SUBMIT_FAILED.
    """
    # Step 1: reconcile against server state. POST timeouts may have left
    # SUBMIT_FAILED entries in the manifest for transformations that actually
    # succeeded server-side; recover their real job IDs by listing all
    # server-side jobs and matching on input_accession.
    try:
        server_jobs = _list_transformations(server, token)
        print(f"[reconcile] listed {len(server_jobs)} transformation(s) from server")
        existing, reconciled_accs = _reconcile_from_server(
            existing, file_jobs, server_jobs,
            config_id, image_name, image_version, memory, volume,
        )
    except Exception as exc:
        print(f"[reconcile] WARNING: couldn't list server-side transformations "
              f"(continuing without reconciliation): {exc}")
        reconciled_accs = set()

    # Step 2: build the existing-by-accession map AFTER reconciliation, so any
    # rescued entries get treated as already-submitted. Treat SUBMIT_FAILED
    # entries as if they don't exist so the retry path still works for cases
    # where the server genuinely never received the request.
    already: dict[str, TransformationJob] = {
        t.input_accession: t for t in existing
        if t.input_accession and t.submit_status != "SUBMIT_FAILED"
    }

    candidates: list[FileJob] = []
    skipped_no_accession: list[str] = []
    skipped_already: list[str] = []
    skipped_not_completed: list[str] = []
    skipped_user: list[str] = []
    for fj in file_jobs:
        if fj.status != "COMPLETED":
            skipped_not_completed.append(fj.plate)
            continue
        if not fj.accession:
            skipped_no_accession.append(fj.plate)
            continue
        if fj.accession in already or fj.accession in reconciled_accs:
            skipped_already.append(fj.plate)
            continue
        if fj.plate in skip_plates:
            skipped_user.append(fj.plate)
            continue
        candidates.append(fj)

    if skipped_not_completed:
        print(f"[transform] skipping {len(skipped_not_completed)} non-completed file jobs "
              f"({', '.join(skipped_not_completed[:3])}{'...' if len(skipped_not_completed) > 3 else ''})")
    if skipped_no_accession:
        print(f"[transform] skipping {len(skipped_no_accession)} file jobs missing accession "
              f"({', '.join(skipped_no_accession[:3])}{'...' if len(skipped_no_accession) > 3 else ''})")
    if skipped_already:
        print(f"[transform] skipping {len(skipped_already)} already-submitted "
              f"({', '.join(skipped_already[:3])}{'...' if len(skipped_already) > 3 else ''})")
    if skipped_user:
        print(f"[transform] skipping {len(skipped_user)} plate(s) per --skip-plates "
              f"({', '.join(skipped_user[:3])}{'...' if len(skipped_user) > 3 else ''})")
    if not candidates:
        print("[transform] nothing to do.")
        return existing

    # Make it impossible to silently double-submit. Always print the full list
    # of candidate accessions before any POST fires. List is deliberately
    # verbose so a re-submission accident is visible at a glance.
    print(f"[transform] ABOUT TO SUBMIT {len(candidates)} transformation(s) "
          f"with config_id={config_id} {image_name}:{image_version} mem={memory} vol={volume}")
    for fj in candidates:
        print(f"[transform]   - {fj.plate}  input_accession={fj.accession}")

    if no_submit:
        # Safety mode: caller explicitly asked us NOT to POST. Reconciliation
        # has already run (it's the first step of this function); the manifest
        # is up-to-date with whatever server state was discoverable. Return
        # without POSTing the candidates so the user can inspect.
        print(f"[transform] --transform-no-submit set; SKIPPING {len(candidates)} new "
              f"submission(s). Re-run without --transform-no-submit if you want to POST.")
        return existing

    # Final gate before POSTing. The server-side LIST endpoint only reports
    # currently-running pods (completed transformations vanish once their Job
    # pods are GC'd), so reconciliation cannot reliably detect transformations
    # that *already finished* outside this manifest. The manifest itself is
    # the source of truth for what *this* run has submitted, and may miss
    # submissions made via the UI / a prior --transform-only invocation that
    # used a different manifest. So when running interactively, require
    # explicit Y before POSTing. In non-interactive (nohup) runs, --yes is
    # mandatory to confirm the candidate list is what the user expects.
    if not auto_confirm:
        if sys.stdin.isatty():
            answer = input(f"[transform] proceed with {len(candidates)} submission(s)? [y/N] ").strip().lower()
            if answer != "y":
                print("[transform] aborted by user; no transformations submitted.")
                return existing
        else:
            print(f"[transform] REFUSING to submit {len(candidates)} transformation(s): "
                  f"running non-interactively without --yes. Re-run with --yes once you've "
                  f"reviewed the candidate list above (and used --skip-plates to exclude any "
                  f"plates already submitted outside this manifest).", file=sys.stderr)
            return existing

    def _submit_one(fj: FileJob) -> TransformationJob:
        tj = TransformationJob(
            plate=fj.plate,
            input_accession=fj.accession or "",
            config_id=config_id,
            image_name=image_name,
            image_version=image_version,
            memory_size=memory,
            volume_size=volume,
        )
        try:
            tj.job_id = _post_transformation(
                server, token, fj.accession or "",
                config_id, image_name, image_version, memory, volume
            )
            tj.submit_status = "SUBMITTED"
            # `state` is unknown at submit time; will be filled in by the
            # poll endpoint. PENDING is the spec's pre-scheduling state and
            # a reasonable optimistic seed.
            tj.state = "PENDING"
            print(f"[transform] {fj.plate}: jobId={tj.job_id} input={fj.accession}")
        except Exception as exc:
            tj.error = str(exc)
            tj.submit_status = "SUBMIT_FAILED"
            print(f"[transform] {fj.plate}: SUBMIT FAILED — {exc}")
        return tj

    new_jobs: list[TransformationJob] = []
    with ThreadPoolExecutor(max_workers=max(1, parallelism)) as ex:
        futures = [ex.submit(_submit_one, fj) for fj in candidates]
        for fut in as_completed(futures):
            new_jobs.append(fut.result())

    # Preserve plate order; keep existing entries that we didn't replace.
    plate_order = {fj.plate: i for i, fj in enumerate(file_jobs)}
    keep_existing = [t for t in existing if t.input_accession not in {nj.input_accession for nj in new_jobs}]
    combined = keep_existing + new_jobs
    combined.sort(key=lambda t: plate_order.get(t.plate, 1_000_000))
    return combined


# State terminology — the file-import API uses STARTING/STARTED/RUNNING +
# COMPLETED/FAILED/CANCELLED ("status"). The transformation API uses
# PENDING/WAITING/RUNNING + DONE/FAILED/UNKNOWN ("state"). The two are kept
# separate because they're truly different vocabularies, even though the
# concept is similar.
TRANSFORM_RUNNING_STATES = {"PENDING", "WAITING", "RUNNING"}
TRANSFORM_TERMINAL_STATES = {"DONE", "FAILED"}


def _summarise_transforms(jobs: list[TransformationJob]) -> str:
    counts: dict[str, int] = {}
    for j in jobs:
        if j.submit_status == "SUBMIT_FAILED":
            counts["SUBMIT_FAILED"] = counts.get("SUBMIT_FAILED", 0) + 1
        else:
            counts[j.state or "UNKNOWN"] = counts.get(j.state or "UNKNOWN", 0) + 1
    return ", ".join(f"{n} {st}" for st, n in sorted(counts.items()))


def watch_transformations(
    server: str, token: str, jobs: list[TransformationJob], poll_s: int = 30,
    on_change=None,
) -> None:
    """Poll transformations until every job is in a terminal state.

    Updates `state`, `state_reason`, `state_description`, `end_time` in place
    on each TransformationJob. Mirrors the structure of `watch_jobs` for file
    imports — initial snapshot, periodic transitions, periodic tally, final
    summary. Transformations typically take hours, so the default 30 s poll
    cadence is plenty.

    `on_change`, if supplied, is invoked after every state transition (and
    once after the initial snapshot) so the manifest can be persisted
    mid-watch — useful when other processes (or the user) are tailing
    progress.

    Skips entries that never got a job_id (SUBMIT_FAILED) or are already in a
    terminal state from a previous run.
    """
    pending: dict[int, TransformationJob] = {
        j.job_id: j for j in jobs
        if j.job_id is not None and (j.state or "PENDING") not in TRANSFORM_TERMINAL_STATES
    }
    if not pending:
        print("[watch-transform] no submitted-but-non-terminal transformations to track")
        return
    print(f"[watch-transform] tracking {len(pending)} transformation(s); polling every {poll_s}s")

    # Initial snapshot so the user sees the current state of every job.
    for job_id, tj in pending.items():
        try:
            body = _get_transformation(server, token, job_id)
        except Exception as exc:
            print(f"[watch-transform] {tj.plate} (#{job_id}) initial poll failed: {exc}")
            continue
        _apply_transform_response(tj, body)
        print(f"[watch-transform] {tj.plate} (#{job_id}): {tj.state}"
              f"{(' (' + tj.state_reason + ')') if tj.state_reason else ''}")
    print(f"[watch-transform] initial: {_summarise_transforms(jobs)}")
    if on_change is not None:
        on_change()

    cycle = 0
    while pending:
        time.sleep(poll_s)
        cycle += 1
        finished_ids: list[int] = []
        changed = False
        for job_id, tj in pending.items():
            try:
                body = _get_transformation(server, token, job_id)
            except Exception as exc:
                print(f"[watch-transform] {tj.plate} (#{job_id}) poll failed: {exc}")
                continue
            prev = tj.state
            _apply_transform_response(tj, body)
            if tj.state != prev:
                print(f"[watch-transform] {tj.plate} (#{job_id}): {prev} -> {tj.state}"
                      f"{(' reason=' + tj.state_reason) if tj.state_reason else ''}")
                changed = True
            if (tj.state or "") in TRANSFORM_TERMINAL_STATES:
                finished_ids.append(job_id)
        for jid in finished_ids:
            del pending[jid]
        if changed and on_change is not None:
            on_change()
        if cycle % 10 == 0 and pending:
            print(f"[watch-transform] cycle {cycle}: {_summarise_transforms(jobs)}")
    print(f"[watch-transform] all transformations terminal: {_summarise_transforms(jobs)}")


def _apply_transform_response(tj: TransformationJob, body: dict) -> None:
    """Copy the relevant fields from a GET /transformations/jobs/{id} body
    onto the manifest's TransformationJob entry. Tolerant of missing keys."""
    status = body.get("status") or {}
    if isinstance(status, dict):
        tj.state = status.get("state") or tj.state
        tj.state_reason = status.get("reason")
        tj.state_description = status.get("description")
    if body.get("create_time"):
        tj.create_time = body["create_time"]
    if body.get("end_time"):
        tj.end_time = body["end_time"]


# ---------------------------------------------------------------------------
# Watching
# ---------------------------------------------------------------------------


def _summarise(jobs: list[FileJob]) -> str:
    """One-line tally of jobs by status for periodic progress prints."""
    counts: dict[str, int] = {}
    for j in jobs:
        counts[j.status or "UNKNOWN"] = counts.get(j.status or "UNKNOWN", 0) + 1
    return ", ".join(f"{n} {st}" for st, n in sorted(counts.items()))


def watch_jobs(
    server: str, token: str, jobs: list[FileJob], poll_s: int = 30,
    on_change=None,
) -> None:
    """Poll until every job is terminal. Updates jobs in place.

    `on_change`, if supplied, is invoked after every status transition (and
    once after the initial snapshot) so callers can persist progress to the
    manifest mid-watch — needed so a parallel `--transform-only` loop can see
    file jobs flip to COMPLETED and queue their transformations without
    waiting for the full batch to finish.
    """
    pending = {j.job_exec_id: j for j in jobs if j.job_exec_id is not None
               and j.status in RUNNING_STATUSES}
    if not pending:
        return
    print(f"[watch] tracking {len(pending)} job(s); polling every {poll_s}s")

    # Initial snapshot: fetch current status for every job and log it once,
    # so the user sees all 14 (or however many) at startup — not just the
    # subset whose status happens to differ from the manifest seed. For any
    # job that's already terminal at snapshot time, also pull the output so
    # the accession lands in the manifest before the first sleep — a parallel
    # --transform-only otherwise sees "COMPLETED with no accession" and skips.
    snapshot_finished: list[int] = []
    for job_id, fj in pending.items():
        try:
            fj.status = _job_status(server, token, job_id)
        except Exception as exc:
            print(f"[watch] {fj.plate} (#{job_id}) initial status check failed: {exc}")
            continue
        print(f"[watch] {fj.plate} (#{job_id}): {fj.status}")
        if fj.status in TERMINAL_STATUSES:
            try:
                output = _job_output(server, token, job_id)
                fj.accession = (output.get("result") or {}).get("accession")
                if fj.status != "COMPLETED":
                    fj.error = str(output.get("errors") or output.get("result") or output)
            except Exception as exc:
                fj.error = f"output fetch failed: {exc}"
            snapshot_finished.append(job_id)
    for jid in snapshot_finished:
        del pending[jid]
    print(f"[watch] initial: {_summarise(jobs)}")
    if on_change is not None:
        on_change()

    cycle = 0
    while pending:
        time.sleep(poll_s)
        cycle += 1
        finished_ids: list[int] = []
        changed = False
        for job_id, fj in pending.items():
            try:
                status = _job_status(server, token, job_id)
            except Exception as exc:
                print(f"[watch] {fj.plate} (#{job_id}) status check failed: {exc}")
                continue
            if status != fj.status:
                print(f"[watch] {fj.plate} (#{job_id}): {fj.status} -> {status}")
                fj.status = status
                changed = True
            if status in TERMINAL_STATUSES:
                try:
                    output = _job_output(server, token, job_id)
                    fj.accession = (output.get("result") or {}).get("accession")
                    if status != "COMPLETED":
                        fj.error = str(output.get("errors") or output.get("result") or output)
                except Exception as exc:
                    fj.error = f"output fetch failed: {exc}"
                finished_ids.append(job_id)
                changed = True
        for jid in finished_ids:
            del pending[jid]
        if changed and on_change is not None:
            on_change()
        # Periodic tally so the user sees forward progress even when no
        # individual job has flipped state in the last poll cycle.
        if cycle % 10 == 0 and pending:
            print(f"[watch] cycle {cycle}: {_summarise(jobs)}")
    print(f"[watch] all jobs terminal: {_summarise(jobs)}")


# ---------------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------------


def write_manifest(path: Path, manifest: Manifest) -> None:
    payload = {
        "server": manifest.server,
        "template_id": manifest.template_id,
        "study_accession": manifest.study_accession,
        "samples_group_accession": manifest.samples_group_accession,
        "libraries_group_accession": manifest.libraries_group_accession,
        "file_jobs": [asdict(j) for j in manifest.file_jobs],
        "transformation_jobs": [asdict(t) for t in manifest.transformation_jobs],
    }
    path.write_text(json.dumps(payload, indent=2))
    print(f"[manifest] wrote {path}")


def load_manifest(path: Path) -> Manifest:
    payload = json.loads(path.read_text())
    return Manifest(
        server=payload["server"],
        template_id=payload["template_id"],
        study_accession=payload.get("study_accession"),
        samples_group_accession=payload.get("samples_group_accession"),
        libraries_group_accession=payload.get("libraries_group_accession"),
        file_jobs=[FileJob(**j) for j in payload.get("file_jobs", [])],
        # Backwards-compat: manifests written before the --transform step exists
        # don't have this key. Default to empty list so old manifests still load.
        transformation_jobs=[TransformationJob(**t) for t in payload.get("transformation_jobs", [])],
    )


def apply_accession_overrides(manifest: Manifest, args) -> None:
    """Stamp CLI-supplied accession overrides onto the manifest in place.

    Lets the user inject accessions they discovered out-of-band (GUI, DB)
    when an earlier run failed to record them. Each override is logged so
    there's a paper trail of what got patched.
    """
    if args.study_accession and args.study_accession != manifest.study_accession:
        print(f"[override] study_accession: {manifest.study_accession!r} -> "
              f"{args.study_accession!r}")
        manifest.study_accession = args.study_accession
    if (args.samples_group_accession and
            args.samples_group_accession != manifest.samples_group_accession):
        print(f"[override] samples_group_accession: "
              f"{manifest.samples_group_accession!r} -> "
              f"{args.samples_group_accession!r}")
        manifest.samples_group_accession = args.samples_group_accession
    if (args.libraries_group_accession and
            args.libraries_group_accession != manifest.libraries_group_accession):
        print(f"[override] libraries_group_accession: "
              f"{manifest.libraries_group_accession!r} -> "
              f"{args.libraries_group_accession!r}")
        manifest.libraries_group_accession = args.libraries_group_accession


# ---------------------------------------------------------------------------
# Entry
# ---------------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--server", required=True,
                    help="ODM base URL, e.g. https://<instance>.example.com")
    ap.add_argument("--token", default=DEFAULT_TOKEN,
                    help="API token (or set GENESTACK_API_TOKEN)")
    ap.add_argument("--study-tsv", default=DEFAULT_STUDY_TSV)
    ap.add_argument("--samples-tsv", default=DEFAULT_SAMPLES_TSV)
    ap.add_argument("--libraries-tsv", default=DEFAULT_LIBRARIES_TSV,
                    help="If provided, also import libraries and link them "
                         "to the sample group. Pass an empty string to skip.")
    ap.add_argument("--template", required=True,
                    help="Template accession applied to study + samples + libraries "
                         "(per-instance state — find via the ODM admin UI)")
    ap.add_argument("--data-class", default=DEFAULT_DATA_CLASS)
    ap.add_argument("--parallelism", "-P", type=int, default=DEFAULT_PARALLELISM,
                    help="Max concurrent file submissions (default %(default)s)")
    ap.add_argument("--manifest", default="tahoe_manifest.json",
                    help="Path to write/read the manifest JSON")
    ap.add_argument("--watch", action="store_true",
                    help="After submitting, poll all jobs until terminal")
    ap.add_argument("--watch-only", action="store_true",
                    help="Skip submission; load existing manifest and watch its jobs")
    ap.add_argument("--ensure-links", action="store_true",
                    help="Load existing manifest and re-establish missing links "
                         "(sample group → study, library group → sample group). "
                         "Idempotent — 409 means already linked, treated as success.")
    ap.add_argument("--add-libraries", action="store_true",
                    help="Load existing manifest, import the libraries TSV, and "
                         "link the resulting library group to the manifest's "
                         "sample group. Use --libraries-tsv to override the URL.")
    ap.add_argument("--files-only", action="store_true",
                    help="Load existing manifest and submit the plate file imports "
                         "against its study_accession. Use when an earlier run "
                         "completed study/samples/libraries but didn't reach the "
                         "file-submission step (e.g. timed out on a link call).")
    ap.add_argument("--plates", default=None,
                    help="Comma-separated plate stems to submit (default: all 14). "
                         "E.g. plate1_..._ParseGigalab,plate2_..._ParseGigalab")
    # Transformation step — runs after file imports are COMPLETED (so we know
    # each file's accession). Two modes:
    #   --transform        : chain after the main flow / --files-only, requires --watch
    #   --transform-only   : standalone, reads manifest and queues transformations
    ap.add_argument("--transform", action="store_true",
                    help="After file imports complete, queue one transformation job per "
                         "imported h5ad attachment. Requires --watch (the transformation "
                         "step needs each file's accession, which is only known after the "
                         "import job completes).")
    ap.add_argument("--transform-only", action="store_true",
                    help="Standalone transformation step: load the manifest and queue "
                         "transformations for any COMPLETED file imports that don't "
                         "already have a successful transformation submission. Idempotent.")
    ap.add_argument("--watch-transforms", action="store_true",
                    help="After queueing transformations, poll their state (via "
                         "GET /api/v1/transformations/jobs/{id}) until each reaches "
                         "DONE or FAILED. Updates the manifest with state, "
                         "state_reason (e.g. OOMKilled), state_description, end_time. "
                         "Pairs with --transform or --transform-only.")
    ap.add_argument("--transform-no-submit", action="store_true",
                    help="Safety mode: reconcile manifest entries against server-side "
                         "transformation state (via GET /transformations/jobs) but DO NOT "
                         "POST any new transformations. Use when you suspect previous POSTs "
                         "may have succeeded server-side despite client-side timeouts and "
                         "want to recover real job IDs without risking duplicate submissions.")
    ap.add_argument("--yes", "-y", action="store_true",
                    help="Skip the interactive confirmation prompt before POSTing "
                         "transformations. Required when running non-interactively (nohup, "
                         "CI) and the script needs to POST anything.")
    ap.add_argument("--skip-plates", default="",
                    help="Comma-separated plate stems to skip during transformation "
                         "submission. Use when some plates were already transformed outside "
                         "this manifest (e.g. via the UI or a prior run) — server-side "
                         "reconciliation can't detect completed-and-GC'd transformations.")
    ap.add_argument("--transform-config-id", type=int, default=None,
                    help="ODM transformation configuration_id to use "
                         "(required when --transform/--transform-only is set; "
                         "per-instance server state).")
    ap.add_argument("--transform-image-name", default=DEFAULT_TRANSFORM_IMAGE_NAME,
                    help="Transformation image name (default %(default)s).")
    ap.add_argument("--transform-image-version", default=DEFAULT_TRANSFORM_IMAGE_VERSION,
                    help="Transformation image version (default %(default)s).")
    ap.add_argument("--transform-memory", default=DEFAULT_TRANSFORM_MEMORY,
                    help="Transformation memory_size (default %(default)s).")
    ap.add_argument("--transform-volume", default=DEFAULT_TRANSFORM_VOLUME,
                    help="Transformation volume_size (default %(default)s).")
    # Manual accession overrides — useful when the manifest is missing
    # accessions (e.g. an earlier run dropped sample group due to a bug)
    # and you've found them via the GUI / SQL. Applied to the loaded
    # manifest before any --ensure-links / --add-libraries action.
    ap.add_argument("--study-accession",
                    help="Override manifest's study_accession (writes back).")
    ap.add_argument("--samples-group-accession",
                    help="Override manifest's samples_group_accession (writes back).")
    ap.add_argument("--libraries-group-accession",
                    help="Override manifest's libraries_group_accession (writes back).")
    args = ap.parse_args()

    if not args.token:
        print("error: missing --token (or GENESTACK_API_TOKEN env var)", file=sys.stderr)
        return 2

    if (args.transform or args.transform_only) and args.transform_config_id is None:
        print("error: --transform-config-id is required when --transform / --transform-only is set",
              file=sys.stderr)
        return 2

    manifest_path = Path(args.manifest)

    def _maybe_run_transform(manifest: Manifest) -> None:
        """Run the transformation step against the manifest's completed file_jobs,
        persist the updated manifest. Caller decides when to invoke; this helper
        centralises the args + write-back boilerplate."""
        manifest.transformation_jobs = submit_transformations(
            manifest.server, args.token, manifest.file_jobs,
            manifest.transformation_jobs,
            args.transform_config_id,
            args.transform_image_name,
            args.transform_image_version,
            args.transform_memory,
            args.transform_volume,
            parallelism=args.parallelism,
            no_submit=args.transform_no_submit,
            auto_confirm=args.yes,
            skip_plates=frozenset(p.strip() for p in (args.skip_plates or "").split(",") if p.strip()),
        )
        write_manifest(manifest_path, manifest)
        if args.watch_transforms:
            watch_transformations(
                manifest.server, args.token, manifest.transformation_jobs,
                on_change=lambda: write_manifest(manifest_path, manifest),
            )
            write_manifest(manifest_path, manifest)

    if args.transform_only:
        if not manifest_path.exists():
            print(f"error: --transform-only requires existing {manifest_path}", file=sys.stderr)
            return 2
        manifest = load_manifest(manifest_path)
        apply_accession_overrides(manifest, args)
        _maybe_run_transform(manifest)
        failed = sum(1 for t in manifest.transformation_jobs if t.submit_status == "SUBMIT_FAILED")
        submitted = sum(1 for t in manifest.transformation_jobs if t.submit_status == "SUBMITTED")
        print(f"[summary] transformation submissions: {submitted} ok, {failed} failed")
        return 0 if failed == 0 else 1

    if args.watch_only:
        if not manifest_path.exists():
            print(f"error: --watch-only requires existing {manifest_path}", file=sys.stderr)
            return 2
        manifest = load_manifest(manifest_path)
        apply_accession_overrides(manifest, args)
        watch_jobs(
            manifest.server, args.token, manifest.file_jobs,
            on_change=lambda: write_manifest(manifest_path, manifest),
        )
        write_manifest(manifest_path, manifest)
        if args.transform:
            _maybe_run_transform(manifest)
        return 0 if all(j.status == "COMPLETED" for j in manifest.file_jobs) else 1

    if args.ensure_links:
        if not manifest_path.exists():
            print(f"error: --ensure-links requires existing {manifest_path}", file=sys.stderr)
            return 2
        manifest = load_manifest(manifest_path)
        apply_accession_overrides(manifest, args)
        ensure_links(manifest.server, args.token, manifest)
        write_manifest(manifest_path, manifest)
        return 0

    if args.add_libraries:
        if not manifest_path.exists():
            print(f"error: --add-libraries requires existing {manifest_path}", file=sys.stderr)
            return 2
        if not args.libraries_tsv:
            print("error: --add-libraries needs --libraries-tsv (or the default)",
                  file=sys.stderr)
            return 2
        manifest = load_manifest(manifest_path)
        apply_accession_overrides(manifest, args)
        if not manifest.samples_group_accession:
            print("error: manifest has no samples_group_accession; "
                  "import samples first (or fix the manifest by running "
                  "the main flow against the existing study).", file=sys.stderr)
            return 2
        try:
            manifest.libraries_group_accession = submit_libraries(
                manifest.server, args.token, args.libraries_tsv,
                manifest.samples_group_accession, args.template
            )
        finally:
            write_manifest(manifest_path, manifest)
        return 0

    plates_to_load = PLATE_FILES
    if args.plates:
        wanted = {p.strip() for p in args.plates.split(",") if p.strip()}
        plates_to_load = [p for p in PLATE_FILES if p["plate"] in wanted]
        if not plates_to_load:
            print(f"error: no plates match {sorted(wanted)}", file=sys.stderr)
            return 2

    if args.files_only:
        if not manifest_path.exists():
            print(f"error: --files-only requires existing {manifest_path}", file=sys.stderr)
            return 2
        manifest = load_manifest(manifest_path)
        apply_accession_overrides(manifest, args)
        if not manifest.study_accession:
            print("error: manifest has no study_accession; cannot submit files",
                  file=sys.stderr)
            return 2
        try:
            manifest.file_jobs = submit_all_files(
                manifest.server, args.token, manifest.study_accession,
                plates_to_load, args.parallelism, args.data_class
            )
        finally:
            write_manifest(manifest_path, manifest)
        submitted = sum(1 for j in manifest.file_jobs if j.job_exec_id is not None)
        failed = [j for j in manifest.file_jobs if j.status == "SUBMIT_FAILED"]
        print(f"\n[summary] submitted {submitted}/{len(manifest.file_jobs)} file jobs"
              f" against study {manifest.study_accession}")
        if failed:
            print(f"[summary] {len(failed)} submit failure(s); see manifest.errors")
        if args.watch:
            watch_jobs(
                manifest.server, args.token, manifest.file_jobs,
                on_change=lambda: write_manifest(manifest_path, manifest),
            )
            write_manifest(manifest_path, manifest)
            completed = sum(1 for j in manifest.file_jobs if j.status == "COMPLETED")
            print(f"[summary] {completed}/{len(manifest.file_jobs)} completed")
            if args.transform:
                _maybe_run_transform(manifest)
            return 0 if completed == len(manifest.file_jobs) else 1
        if args.transform:
            # --transform without --watch can't queue transformations because we
            # don't have accessions yet — but the user clearly asked for it, so
            # be explicit rather than silently ignoring.
            print("[hint] --transform requires --watch (or follow up with --transform-only "
                  "after --watch-only completes)")
        print("[hint] run again with --watch-only to poll jobs to completion")
        return 0 if not failed else 1

    manifest = Manifest(server=args.server, template_id=args.template)

    try:
        manifest.study_accession = submit_study(
            args.server, args.token, args.study_tsv, args.template
        )
        manifest.samples_group_accession = submit_samples(
            args.server, args.token, args.samples_tsv,
            manifest.study_accession, args.template
        )
        if args.libraries_tsv:
            manifest.libraries_group_accession = submit_libraries(
                args.server, args.token, args.libraries_tsv,
                manifest.samples_group_accession, args.template
            )
        manifest.file_jobs = submit_all_files(
            args.server, args.token, manifest.study_accession,
            plates_to_load, args.parallelism, args.data_class
        )
    finally:
        # Always persist what we have, even on partial failure.
        write_manifest(manifest_path, manifest)

    submitted = sum(1 for j in manifest.file_jobs if j.job_exec_id is not None)
    failed = [j for j in manifest.file_jobs if j.status == "SUBMIT_FAILED"]
    print(f"\n[summary] submitted {submitted}/{len(manifest.file_jobs)} file jobs"
          f" against study {manifest.study_accession}")
    if failed:
        print(f"[summary] {len(failed)} submit failure(s); see manifest.errors")

    if args.watch:
        watch_jobs(
            args.server, args.token, manifest.file_jobs,
            on_change=lambda: write_manifest(manifest_path, manifest),
        )
        write_manifest(manifest_path, manifest)
        completed = sum(1 for j in manifest.file_jobs if j.status == "COMPLETED")
        print(f"[summary] {completed}/{len(manifest.file_jobs)} completed")
        if args.transform:
            _maybe_run_transform(manifest)
        return 0 if completed == len(manifest.file_jobs) else 1

    if args.transform:
        # Same hint as in --files-only: transformations need accessions which
        # only get filled in by --watch. Surface this explicitly so the user
        # doesn't think --transform was silently ignored.
        print("[hint] --transform requires --watch (or follow up with --transform-only "
              "after --watch-only completes)")
    print("[hint] run again with --watch-only to poll jobs to completion")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
