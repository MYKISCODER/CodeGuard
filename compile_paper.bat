@echo off
REM LaTeX Compilation Script for NeurIPS 2026 Submission (Windows)
REM This script performs the standard 4-step LaTeX compilation process

echo ==========================================
echo NeurIPS 2026 Paper Compilation Script
echo ==========================================
echo.

REM Check if pdflatex is available
where pdflatex >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: pdflatex not found!
    echo.
    echo Please install a LaTeX distribution:
    echo   - MiKTeX: https://miktex.org/
    echo   - TeX Live: https://www.tug.org/texlive/
    echo.
    pause
    exit /b 1
)

REM Check if bibtex is available
where bibtex >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: bibtex not found!
    echo Please install a complete LaTeX distribution.
    pause
    exit /b 1
)

REM Check if the main tex file exists
if not exist "paper_neurips_main.tex" (
    echo ERROR: paper_neurips_main.tex not found!
    echo Please run this script from the project root directory.
    pause
    exit /b 1
)

REM Check if neurips_2026.sty exists
if not exist "neurips_2026.sty" (
    echo WARNING: neurips_2026.sty not found!
    echo Please download the NeurIPS 2026 style file from:
    echo   https://neurips.cc/Conferences/2026/PaperInformation/StyleFiles
    echo.
    set /p continue="Continue anyway? (y/n): "
    if /i not "%continue%"=="y" exit /b 1
)

REM Check if figure files exist
echo Checking for required figure files...
set missing_figs=0
if not exist "figs\fig1_clp_threat_space.pdf" (
    echo   WARNING: figs\fig1_clp_threat_space.pdf not found
    set /a missing_figs+=1
) else (
    echo   OK figs\fig1_clp_threat_space.pdf found
)
if not exist "figs\fig2_system_arch.pdf" (
    echo   WARNING: figs\fig2_system_arch.pdf not found
    set /a missing_figs+=1
) else (
    echo   OK figs\fig2_system_arch.pdf found
)
if not exist "figs\fig3_judge_instability.png" (
    echo   WARNING: figs\fig3_judge_instability.png not found
    set /a missing_figs+=1
) else (
    echo   OK figs\fig3_judge_instability.png found
)

if %missing_figs% GTR 0 (
    echo.
    echo WARNING: %missing_figs% figure file(s) missing!
    echo The compilation will show '??' for missing figures.
    echo See figs\README.md for figure requirements.
    echo.
    set /p continue="Continue anyway? (y/n): "
    if /i not "%continue%"=="y" exit /b 1
)

echo.
echo Starting compilation...
echo.

REM Step 1: First pdflatex pass
echo Step 1/4: Running pdflatex (first pass)...
pdflatex -interaction=nonstopmode paper_neurips_main.tex > compile_step1.log 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: First pdflatex pass failed!
    echo Check compile_step1.log for details.
    type compile_step1.log | more
    pause
    exit /b 1
)
echo   OK First pass completed

REM Step 2: BibTeX
echo Step 2/4: Running bibtex...
bibtex paper_neurips_main > compile_step2.log 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: BibTeX encountered issues (this may be normal if no citations yet)
    echo Check compile_step2.log for details.
)
echo   OK BibTeX completed

REM Step 3: Second pdflatex pass
echo Step 3/4: Running pdflatex (second pass)...
pdflatex -interaction=nonstopmode paper_neurips_main.tex > compile_step3.log 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Second pdflatex pass failed!
    echo Check compile_step3.log for details.
    type compile_step3.log | more
    pause
    exit /b 1
)
echo   OK Second pass completed

REM Step 4: Third pdflatex pass
echo Step 4/4: Running pdflatex (third pass)...
pdflatex -interaction=nonstopmode paper_neurips_main.tex > compile_step4.log 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Third pdflatex pass failed!
    echo Check compile_step4.log for details.
    type compile_step4.log | more
    pause
    exit /b 1
)
echo   OK Third pass completed

echo.
echo ==========================================
echo Compilation completed successfully!
echo ==========================================
echo.
echo Output file: paper_neurips_main.pdf
echo.

REM Check PDF file size
if exist "paper_neurips_main.pdf" (
    for %%A in (paper_neurips_main.pdf) do echo PDF size: %%~zA bytes
)

echo.
echo Next steps:
echo   1. Open paper_neurips_main.pdf to review
echo   2. Check that main content is ^<= 9 pages
echo   3. Verify all figures appear correctly (no '??')
echo   4. Check for overfull hbox warnings in compile logs
echo.
pause
