set -e
S="/c/Program Files/LibreOffice/program/soffice.exe"
for n in 1 2 3; do
  python build_report.py >/dev/null
  "$S" --headless --convert-to pdf MST_Clustering_Mini_Project_Report.docx >/dev/null 2>&1
  python tocgen.py
done
python -c "import fitz;print(len(fitz.open('MST_Clustering_Mini_Project_Report.pdf')))"
