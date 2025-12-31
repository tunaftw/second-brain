# Phase 5: Claude Code Skills Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create Claude Code skills for standardized podcast nuggets workflows.

**Architecture:** Skills are Markdown files in `.claude/skills/` that Claude Code can invoke. Each skill provides structured guidance for a specific workflow.

**Tech Stack:** Markdown skill files, CLI commands

---

## Task 1: Create Skills Directory Structure

**Files:**
- Create: `.claude/skills/nuggets-ingest.md`
- Create: `.claude/skills/nuggets-curate.md`
- Create: `.claude/skills/nuggets-reflect.md`

---

## Task 2: Create Ingest Skill

**File:** `.claude/skills/nuggets-ingest.md`

The ingest skill guides processing new YouTube videos or podcasts.

---

## Task 3: Create Curate Skill

**File:** `.claude/skills/nuggets-curate.md`

The curate skill guides reviewing and rating nuggets.

---

## Task 4: Create Reflect Skill

**File:** `.claude/skills/nuggets-reflect.md`

The reflect skill enables querying and discussing the knowledge library.

---

## Task 5: Update CLAUDE.md

Add skills documentation to the project instructions.

---

## Summary

Phase 5 complete. Skills available:

- `/nuggets-ingest` - Process new content
- `/nuggets-curate` - Review and rate nuggets
- `/nuggets-reflect` - Query the library
