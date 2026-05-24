@echo off
:: Author: RKOJ-ELENO :: 2026-05-24
:: One-click wrapper for bats\jb-publish.ps1. Optional first arg = commit
:: message. Run from a normal terminal in any folder.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0jb-publish.ps1" -Message "%~1"
