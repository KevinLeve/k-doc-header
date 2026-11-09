# K-Doc Header

Drag-and-drop Windows app that detects manually-formatted headings in a
Word manuscript (right font/size/bold, but never tagged with Word's
heading styles) and reapplies the matching named heading style, so
Word's Navigation Pane and auto-generated Table of Contents work.

## Usage

Drop a `.docx` onto the app window, or use **Choose Files...**. It saves
`<name>_styled.docx` next to the original — the input file is never
modified.

Heading styles are matched against a learned "signature map"
(`signature_map.json`) built from a set of correctly-styled reference
documents. If you're working with documents from a different template,
rebuild the map:

```bash
python build_signature_map.py path/to/reference_docs_folder
```

## Running from source

```bash
pip install -r requirements.txt
python app.py
```

## Building

Portable executable:

```bash
pip install pyinstaller
pyinstaller --noconfirm --clean packaging/kdoc_header.spec --distpath dist --workpath build
```

Installer (requires [Inno Setup](https://jrsoftware.org/isinfo.php)):

```bash
pyinstaller --noconfirm --clean packaging/kdoc_header.spec --distpath dist-final --workpath build-final
ISCC.exe packaging/kdoc_header.iss
```
