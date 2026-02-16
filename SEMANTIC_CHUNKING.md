# Semantic Chunking Enhancement

## Overview

The RAG system now uses **intelligent semantic chunking** instead of fixed character-based splitting. This significantly improves retrieval quality by preserving contextual meaning.

## How It Works

### Document-Type Specific Chunking

**Text Files (.txt) & DOCX Documents:**
- Uses `SemanticChunker` with embedding-based boundary detection
- Analyzes semantic similarity between adjacent sentences
- Splits at natural topic/context boundaries (80th percentile threshold)
- Preserves complete thoughts and context
- **Result:** Better context preservation, more meaningful chunks

**PDF Documents:**
- Uses `RecursiveCharacterTextSplitter` with intelligent separators
- Respects document structure (sections → paragraphs → sentences)
- 1000 character chunks with 200 character overlap
- **Result:** Maintains document hierarchy and flow

**CSV Files:**
- Uses optimized smaller chunks (500 chars, 50 overlap)
- Preserves row-level data integrity
- **Result:** Each chunk contains complete, queryable records

### Semantic Chunker Details

The semantic chunker:
1. Embeds each sentence using FastEmbed
2. Calculates cosine similarity between adjacent sentences
3. Identifies semantic "distance" (topic changes)
4. Splits at the top 20% of semantic differences (configurable)
5. Creates chunks at natural topic boundaries

### Benefits Over Fixed Chunking

| Fixed Character Chunking | Semantic Chunking |
|-------------------------|-------------------|
| Arbitrary splits at character limits | Natural splits at topic boundaries |
| May cut sentences mid-thought | Preserves complete semantic units |
| Same strategy for all documents | Adaptive per document type |
| No context awareness | Embedding-based context detection |

## Configuration

Edit [config.json](config.json):

```json
{
    "rag_options": {
        "chunking_strategy": "semantic",
        "semantic_breakpoint_threshold": 80
    }
}
```

- `semantic_breakpoint_threshold`: Percentile threshold (80 = split at top 20% of differences)
  - Higher = fewer, larger chunks (more context)
  - Lower = more, smaller chunks (more precise matching)

## Logging

When uploading documents, logs show chunking details:

```
INFO: Using semantic chunking for text/DOCX document
INFO: Split document into 12 semantic chunks
INFO: Average chunk size: 847 characters
INFO: Added document to the database.
```

## Performance Impact

- **Slightly slower ingestion** (due to embedding calculation during chunking)
- **Significantly better retrieval quality** (more relevant context returned)
- **Trade-off:** Worth the extra processing time for improved RAG accuracy

## Technical Implementation

Located in [ragapp/rag_handler.py](ragapp/rag_handler.py):

1. `_initialize_splitters()` - Sets up document-specific splitters
2. `_get_splitter_for_document()` - Selects appropriate strategy
3. `add_document_to_chroma()` - Applies selected chunking and logs metrics

## Rebuild Instructions

```bash
# Rebuild with new dependencies
docker build -t rag_django:1.0.0 .

# Restart
docker-compose restart web

# Or full restart
docker-compose down && docker-compose up
```

## Example: Semantic vs Fixed Chunking

### Fixed Character Chunking (Old):
```
Chunk 1: "...project deadline. The budget for this initiative is $500,000 and we 
         need to allocate resources carefully. The technical stack includes Django,"
Chunk 2: "Python, and PostgreSQL. All developers must follow coding standards..."
```
❌ Splits mid-topic, breaks context

### Semantic Chunking (New):
```
Chunk 1: "...project deadline. The budget for this initiative is $500,000 and we 
          need to allocate resources carefully."
Chunk 2: "The technical stack includes Django, Python, and PostgreSQL. All 
          developers must follow coding standards..."
```
✅ Natural topic boundary, preserves context

## Monitoring Chunk Quality

Check logs after upload to see:
- Chunking strategy used
- Number of chunks created
- Average chunk size

Adjust `semantic_breakpoint_threshold` if chunks are too large/small.
