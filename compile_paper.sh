#!/bin/bash
# LaTeX Compilation Script for NeurIPS 2026 Submission
# This script performs the standard 4-step LaTeX compilation process

echo "=========================================="
echo "NeurIPS 2026 Paper Compilation Script"
echo "=========================================="
echo ""

# Check if pdflatex is available
if ! command -v pdflatex &> /dev/null; then
    echo "ERROR: pdflatex not found!"
    echo ""
    echo "Please install a LaTeX distribution:"
    echo "  - Windows: MiKTeX (https://miktex.org/) or TeX Live (https://www.tug.org/texlive/)"
    echo "  - macOS: MacTeX (https://www.tug.org/mactex/)"
    echo "  - Linux: sudo apt-get install texlive-full"
    echo ""
    exit 1
fi

# Check if bibtex is available
if ! command -v bibtex &> /dev/null; then
    echo "ERROR: bibtex not found!"
    echo "Please install a complete LaTeX distribution."
    exit 1
fi

# Check if the main tex file exists
if [ ! -f "paper_neurips_main.tex" ]; then
    echo "ERROR: paper_neurips_main.tex not found!"
    echo "Please run this script from the project root directory."
    exit 1
fi

# Check if neurips_2026.sty exists
if [ ! -f "neurips_2026.sty" ]; then
    echo "WARNING: neurips_2026.sty not found!"
    echo "Please download the NeurIPS 2026 style file from:"
    echo "  https://neurips.cc/Conferences/2026/PaperInformation/StyleFiles"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if figure files exist
echo "Checking for required figure files..."
missing_figs=0
for fig in "figs/fig1_clp_threat_space.pdf" "figs/fig2_system_arch.pdf" "figs/fig3_judge_instability.png"; do
    if [ ! -f "$fig" ]; then
        echo "  WARNING: $fig not found"
        missing_figs=$((missing_figs + 1))
    else
        echo "  ✓ $fig found"
    fi
done

if [ $missing_figs -gt 0 ]; then
    echo ""
    echo "WARNING: $missing_figs figure file(s) missing!"
    echo "The compilation will show '??' for missing figures."
    echo "See figs/README.md for figure requirements."
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "Starting compilation..."
echo ""

# Step 1: First pdflatex pass
echo "Step 1/4: Running pdflatex (first pass)..."
pdflatex -interaction=nonstopmode paper_neurips_main.tex > compile_step1.log 2>&1
if [ $? -ne 0 ]; then
    echo "ERROR: First pdflatex pass failed!"
    echo "Check compile_step1.log for details."
    tail -50 compile_step1.log
    exit 1
fi
echo "  ✓ First pass completed"

# Step 2: BibTeX
echo "Step 2/4: Running bibtex..."
bibtex paper_neurips_main > compile_step2.log 2>&1
if [ $? -ne 0 ]; then
    echo "WARNING: BibTeX encountered issues (this may be normal if no citations yet)"
    echo "Check compile_step2.log for details."
fi
echo "  ✓ BibTeX completed"

# Step 3: Second pdflatex pass
echo "Step 3/4: Running pdflatex (second pass)..."
pdflatex -interaction=nonstopmode paper_neurips_main.tex > compile_step3.log 2>&1
if [ $? -ne 0 ]; then
    echo "ERROR: Second pdflatex pass failed!"
    echo "Check compile_step3.log for details."
    tail -50 compile_step3.log
    exit 1
fi
echo "  ✓ Second pass completed"

# Step 4: Third pdflatex pass
echo "Step 4/4: Running pdflatex (third pass)..."
pdflatex -interaction=nonstopmode paper_neurips_main.tex > compile_step4.log 2>&1
if [ $? -ne 0 ]; then
    echo "ERROR: Third pdflatex pass failed!"
    echo "Check compile_step4.log for details."
    tail -50 compile_step4.log
    exit 1
fi
echo "  ✓ Third pass completed"

echo ""
echo "=========================================="
echo "Compilation completed successfully!"
echo "=========================================="
echo ""
echo "Output file: paper_neurips_main.pdf"
echo ""

# Check PDF file size
if [ -f "paper_neurips_main.pdf" ]; then
    pdf_size=$(du -h paper_neurips_main.pdf | cut -f1)
    echo "PDF size: $pdf_size"

    # Count pages (if pdfinfo is available)
    if command -v pdfinfo &> /dev/null; then
        pages=$(pdfinfo paper_neurips_main.pdf 2>/dev/null | grep "Pages:" | awk '{print $2}')
        if [ ! -z "$pages" ]; then
            echo "Total pages: $pages"
            echo ""
            echo "IMPORTANT: NeurIPS requires main content ≤ 9 pages"
            echo "           (References, Checklist, Appendix not counted)"
        fi
    fi
fi

echo ""
echo "Next steps:"
echo "  1. Open paper_neurips_main.pdf to review"
echo "  2. Check that main content is ≤ 9 pages"
echo "  3. Verify all figures appear correctly (no '??')"
echo "  4. Check for overfull hbox warnings in compile logs"
echo ""
