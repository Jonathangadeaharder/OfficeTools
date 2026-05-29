---
id: TDD-OFTC
kind: tdd
title: OfficeTools
description: >-
  Collection of 14 Python CLI/GUI tools for PDF, audio, video, and ebook
  processing
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

OfficeTools is a collection of 14 independent Python CLI/GUI tools for PDF, audio, video, and ebook processing with consistent per-tool hygiene (ruff, pyright, hatchling) and 5 ADRs documenting architecture decisions. However, it is the only project in this audit with absolutely no CI/CD pipeline -- zero automation for linting, testing, or releases. No test infrastructure is visible across any tool. macOS .app bundle notarization status is unknown. Heavy dependencies (docling[vlm] + mlx-vlm) in pdf2md create platform lock-in. Recommendation: add CI/CD, establish test infrastructure, document system dependencies.

## Scope

Assessed: 14 tools (pdf2md, pdfcompress, pdfconcat, pdfsplit, pdfocr, ebooktool, mp4audio, mp4subs, videogui, docgui, officetools orchestrator), macOS .app bundle at apps/Doc Tools.app/, 5 ADRs in docs/architecture/. Excluded: cross-tool integration testing, Homebrew distribution, Docker deployment, Windows/Linux compatibility.

## Architecture

Each tool is a fully independent uv-managed Python package with its own pyproject.toml, uv.lock, and dependency graph. No shared workspace or common library -- each tool self-contained. officetools CLI discovers and invokes tools via subprocess. Some tools offer dual CLI + GUI (tkinter) interfaces. 5 ADRs cover: monorepo design using uv, tool isolation rationale, orchestrator CLI pattern, build/packaging strategy, and tool discovery mechanism.

## Tech Stack

Python >=3.10, uv, hatchling, ruff, pyright, pytest across all tools. Per-tool deps: pikepdf (3 tools), rich (3 tools), docling[vlm] + mlx-vlm (pdf2md), ocrmypdf (pdfocr), ebooklib + fpdf2 + markdown (ebooktool). Zero-dependency tools: mp4audio, mp4subs, videogui, docgui, officetools. tkinter for GUI tools. macOS .app bundle wraps docgui and related tools.

## Code Quality

Consistent tooling across all packages: ruff check + ruff format + pyright + pytest. AGENTS.md documents the development workflow. 5 ADRs are well-structured. No CI/CD means zero automated quality enforcement. No coverage targets in any pyproject.toml. No pre-commit hooks. No mutation testing. Some tools declare zero dependencies but may rely on undocumented system tools (ffmpeg, etc.).

## Security

ruff security rules in lint pass. pyright for basic type correctness. No SAST, no secret scanning, no dependency vulnerability scanning. ocrmypdf requires system Tesseract -- version-dependent security profile. docling[vlm] parses arbitrary documents -- potential for document-based exploits. tkinter GUIs have no sandboxing. macOS bundle notarization status unknown -- un-notarized apps trigger Gatekeeper warnings.

## Scalability & Performance

Single-process CLI/GUI tools -- no server or concurrent access concerns. Performance bounded by document size and model inference. pdf2md with docling[vlm] + mlx-vlm will be slow and memory-intensive on large documents. No benchmarks exist for any tool.

## Operations & DevOps

NO CI/CD pipeline. Zero GitHub Actions workflows. No automated quality checks. No release automation. macOS .app bundle likely not notarized. No Homebrew formula or other distribution channel beyond git clone. No Dockerfile. No Makefile at repository level.

## Dependencies & Third-Party Risk

pikepdf duplicated across 3 tools (version drift risk without shared library). docling[vlm] is an extremely heavy dependency for PDF-to-markdown conversion. mlx-vlm is Apple Silicon only -- pdf2md non-functional on x86 or Linux. ocrmypdf requires system Tesseract installation (undocumented). 5 zero-dependency tools may rely on undocumented ffmpeg/system tools. 11 independent lock files to maintain. Tool versions range from 0.1.0 to 0.1.1 with no documented release strategy.

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| No CI/CD pipeline | High | High | Add GitHub Actions with ruff+pyright+pytest within 1 month |
| No test infrastructure visible | High | High | Add pytest config with coverage to each tool within 1 month |
| Heavy deps in pdf2md (docling+vlm) | Medium | Medium | Evaluate lighter alternatives for PDF-to-markdown |
| macOS bundle notarization unknown | Medium | Medium | Verify or document notarization status |
| System deps undocumented (ffmpeg, Tesseract) | Medium | Medium | Document per-tool system requirements in metadata |
| 11 independent lock files | Medium | Low | Evaluate uv workspace for shared dependency management |
| pikepdf duplicated across 3 tools | Low | Low | Create officetools-core shared package |

## Recommendations

1. Add GitHub Actions CI with ruff check + pyright + pytest for all tools within 1 month (P0).
2. Add pytest configuration with 90% branch coverage targets to each pyproject.toml within 1 month (P0).
3. Document system dependencies (Tesseract, ffmpeg, etc.) in each tool's metadata within 1 month (P1).
4. Verify or complete macOS .app bundle notarization within 1 month (P1).
5. Create officetools-core shared package for common PDF utilities within 1 quarter (P1).
6. Evaluate lighter alternatives to docling[vlm] for pdf2md within 1 quarter (P2).
7. Add monorepo-level Makefile for running all checks across all tools within 1 quarter (P2).
