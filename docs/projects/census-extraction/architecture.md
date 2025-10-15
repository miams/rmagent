# RM11 census extraction architecture diagram

```mermaid
flowchart TD
    subgraph Ingestion["Ingestion layer"]
        RMDB[RootsMagic Media Links]
        Meta[Media catalog & census configs]
        RMDB --> Catalog[Ingestion orchestrator]
        Meta --> Catalog
    end

    subgraph Preprocess["Preprocessing & layout"]
        Catalog --> PreProc[OpenCV preprocessing\n(deskew, denoise, CLAHE)]
        PreProc --> Layout[Layout segmentation\n(doctr/layoutparser)]
        Layout --> Cells[Cell metadata & crops]
    end

    subgraph OCR["OCR & handwriting recognition"]
        Cells --> OCRRouter[Model routing\n(confidence thresholds)]
        OCRRouter --> Tesseract[Tesseract OCR]
        OCRRouter --> Kraken[Kraken/Calamari HTR]
        OCRRouter --> VisionLLM[Vision LLM fallback\n(GPT-4o / Claude 3.5)]
        Tesseract --> OCRResults[Token-level text + confidence]
        Kraken --> OCRResults
        VisionLLM --> OCRResults
    end

    subgraph Parsing["Parsing & entity matching"]
        OCRResults --> Parse[Per-year parsers\n(normalize columns)]
        Parse --> Match[Match to RootsMagic PersonID\n(RapidFuzz, heuristics)]
        Match --> SidecarWriter[Sidecar writer\n(sqlite-utils)]
    end

    subgraph Review["Human-in-the-loop review"]
        Cells --> ReviewUI[FastAPI + HTMX UI\n(Image snippets + forms)]
        Match --> ReviewUI
        ReviewUI --> Corrections[Reviewer decisions]
        Corrections --> SidecarWriter
    end

    SidecarWriter --> SidecarDB[(Census sidecar SQLite)]
    SidecarDB --> Analytics[Analytics & exports\n(pandas, reporting scripts)]
    SidecarDB --> LangChainTools[LangChain tools\n(query_census_entries, etc.)]
    LangChainTools --> RMAgent[RMAgent agents & CLI]
    Analytics --> RMAgent
```
