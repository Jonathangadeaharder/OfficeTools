---
id: TDD-OFTC
kind: tdd
title: OfficeTools
description: >-
  Collection of 11 Python CLI/GUI tools + 1 orchestrator for PDF, audio, video,
  and ebook processing
status: draft
date: 2026-05-17T00:00:00.000Z
authors: []
reviewers: []
risk_level: high
scope_type: project
tags:
  - python
  - pdf
  - audio
  - video
  - gui
  - cli
related: []
checksum: 9749ba267bd229fcc5cefedd61704c7e1a600e4154ae76a9c18110d3ecccf171
---

## Executive Summary

OfficeTools is a collection of 11 independent Python CLI/GUI tools plus 1 orchestrator CLI for PDF, audio, video, and ebook processing with consistent per-tool hygiene (ruff, pyright, hatchling) and 5 ADRs documenting architecture decisions. CI/CD is now in place with 3 GitHub Actions workflows (pr-gate, merge-gate, sonarcloud) covering linting, type checking, testing, dependency scanning (Trivy), secret scanning (Gitleaks), and SAST (CodeQL). No test infrastructure is visible across any tool. macOS .app bundle notarization status is unknown. Heavy dependencies (docling[vlm] + mlx-vlm) in pdf2md create platform lock-in. Recommendation: establish test infrastructure, document system dependencies, add videocompress to CI matrix.

## Scope

Assessed: 11 tools + 1 orchestrator (pdf2md, pdfcompress, pdfconcat, pdfsplit, pdfocr, ebooktool, mp4audio, mp4subs, videocompress, videogui, docgui, officetools orchestrator), macOS .app bundles at apps/Doc Tools.app/ and apps/Video Tools.app/, 5 ADRs in docs/architecture/, 3 GitHub Actions workflows. Excluded: cross-tool integration testing, Homebrew distribution, Docker deployment, Windows/Linux compatibility.

## Architecture

Each tool is a fully independent uv-managed Python package with its own pyproject.toml, uv.lock, and dependency graph. No shared workspace or common library -- each tool self-contained. The officetools CLI (not a shared library) discovers and invokes tools via subprocess. Some tools offer dual CLI + GUI (tkinter) interfaces. 5 ADRs cover: monorepo design using uv, tool isolation rationale, orchestrator CLI pattern, build/packaging strategy, and tool discovery mechanism.

## Tech Stack

Python >=3.10, uv, hatchling, ruff, pyright, pytest across all tools. Per-tool deps: pikepdf (3 tools), rich (3 tools), docling[vlm] + fpdf2 + mlx-vlm (pdf2md), ocrmypdf (pdfocr), ebooklib + fpdf2 + markdown (ebooktool). Zero-dependency tools: mp4audio, mp4subs, videogui, videocompress, docgui, officetools. tkinter for GUI tools. macOS .app bundles wrap docgui and videogui (Doc Tools.app, Video Tools.app).

## Code Quality

Consistent tooling across all packages: ruff check + ruff format + pyright + pytest. AGENTS.md documents the development workflow. 5 ADRs are well-structured. CI/CD is in place (pr-gate + merge-gate + sonarcloud workflows) with automated linting, type checking, testing, Trivy dependency scanning, Gitleaks secret scanning, and CodeQL SAST. No coverage targets in any pyproject.toml. No pre-commit hooks. No mutation testing. No test directories exist yet. Some tools declare zero dependencies but may rely on undocumented system tools (ffmpeg, etc.). videocompress is missing from the CI matrix.

## Security

ruff security rules in lint pass. pyright for basic type correctness. Trivy for dependency vulnerability scanning. Gitleaks for secret scanning. CodeQL for SAST on merge to main. ocrmypdf requires system Tesseract -- version-dependent security profile. docling[vlm] parses arbitrary documents -- potential for document-based exploits. tkinter GUIs have no sandboxing. macOS bundle notarization status unknown -- un-notarized apps trigger Gatekeeper warnings.

## Scalability & Performance

Single-process CLI/GUI tools -- no server or concurrent access concerns. Performance bounded by document size and model inference. pdf2md with docling[vlm] + mlx-vlm will be slow and memory-intensive on large documents. No benchmarks exist for any tool.

## Operations & DevOps

CI/CD pipeline is in place with 3 GitHub Actions workflows. pr-gate.yml runs per-package lint (ruff), type check (pyright), tests (pytest with 90% branch coverage gate), Trivy dependency scan, and Gitleaks secret scan on pull requests. merge-gate.yml adds CodeQL SAST on push to main. sonarcloud.yml runs SonarCloud analysis. No release automation. macOS .app bundles likely not notarized. No Homebrew formula or other distribution channel beyond git clone. No Dockerfile. No Makefile at repository level.

## Dependencies & Third-Party Risk

pikepdf duplicated across 3 tools (version drift risk without shared library). docling[vlm] is an extremely heavy dependency for PDF-to-markdown conversion. mlx-vlm is Apple Silicon only -- pdf2md non-functional on x86 or Linux. ocrmypdf requires system Tesseract installation (undocumented). 6 zero-dependency tools may rely on undocumented ffmpeg/system tools. 11 independent lock files (videocompress is missing its uv.lock). Tool versions range from 0.1.0 to 0.1.1 with no documented release strategy.

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| No test infrastructure visible | High | High | Add pytest config with coverage to each tool within 1 month |
| Heavy deps in pdf2md (docling+vlm) | Medium | Medium | Evaluate lighter alternatives for PDF-to-markdown |
| macOS bundle notarization unknown | Medium | Medium | Verify or document notarization status |
| System deps undocumented (ffmpeg, Tesseract) | Medium | Medium | Document per-tool system requirements in metadata |
| videocompress missing from CI matrix | Medium | Low | Add videocompress to pr-gate/merge-gate workflow matrix |
| videocompress missing uv.lock | Medium | Low | Run `uv sync` in videocompress/ to generate lock file |
| 11 independent lock files | Medium | Low | Evaluate uv workspace for shared dependency management |
| pikepdf duplicated across 3 tools | Low | Low | Create officetools-core shared package |

## Recommendations

1. Add pytest configuration with 90% branch coverage targets to each pyproject.toml, plus test directories with initial tests, within 1 month (P0).
2. Add videocompress to the CI matrix in pr-gate.yml and merge-gate.yml within 1 week (P0).
3. Generate uv.lock for videocompress by running `uv sync` within 1 week (P0).
4. Document system dependencies (Tesseract, ffmpeg, etc.) in each tool's metadata within 1 month (P1).
5. Verify or complete macOS .app bundle notarization within 1 month (P1).
6. Create officetools-core shared package for common PDF utilities within 1 quarter (P1).
7. Evaluate lighter alternatives to docling[vlm] for pdf2md within 1 quarter (P2).
8. Add monorepo-level Makefile for running all checks across all tools within 1 quarter (P2).
