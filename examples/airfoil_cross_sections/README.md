---
title: "Batch Cross-sectional Analyses"
subtitle: ""
short_title: "Batch Cross-sectional Analyses"
description: 
authors:
  - name: Su Tian
    affiliations:
      - AnalySwift
date: 2026-05-11
banner: 
label: "batch-cs-analysis"
tags:
  - vabs
  - prevabs
  - composites
  - beam
  - 2dsg
  - airfoil
keywords:
  - VABS
  - Composite Slender Structure
  - Beam Model Properties
  - Airfoil
---

# Batch Cross-sectional Analyses

## Overview

## File Structure

## Running This Example

## Analysis Workflow Scripting

## Results and Visualization

## Configuration Reference

`run.py` supports loading a JSON config file such as `config.json`. Relative paths are resolved relative to the config file location.

- `airfoil_dir`: directory containing candidate airfoil coordinate files.
- `working_dir`: output directory for per-airfoil case folders, logs, and the aggregated CSV.
- `airfoil_files`: optional explicit list of airfoil filenames or paths to run. If omitted, all files under `airfoil_dir` are considered.
- `sample_size`: optional random sample count taken from the selected airfoils.
- `seed`: random seed used with `sample_size`.
- `jobs`: number of airfoils to run concurrently through the async batch scheduler.
- `solver_timeout`: optional timeout in seconds applied independently to each `prevabs` and `vabs` command.
- `failed_case`: failure policy, either `continue` or `stop`.
- `properties`: list of section properties to extract from VABS output, such as `mu`, `ea`, `gj`, `ei22`, and `ei33`.
- `output_csv`: output CSV filename or path. When running from `config.json`, relative paths are resolved next to the config file rather than under `working_dir`. The file is initialized at run start and appended after each completed case.
- `template_file`: PreVABS XML template used for each case.
- `material_file`: optional material database copied into each case directory.
- `template_params`: extra template placeholders passed into the XML render step. Common keys in this example include `mesh_size`, `element_shape`, `element_type`, `translate_x`, `translate_y`, `scale`, and `lamina_thickness`. These values override the defaults defined in `main.py`.
