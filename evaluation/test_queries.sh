#!/bin/bash

# Test query service
echo "================================"
echo "Testing Document Query"
echo "================================"
echo ""

BASE_URL="http://localhost:8001"

# Test 1: Health check
echo "1. Health Check"
curl -s "${BASE_URL}/health" | jq '.'
echo -e "\n"

# Test 2: List all documents
echo "2. List all documents"
curl -s "${BASE_URL}/documents" | jq '.'
echo -e "\n"

# Test 3: Query - General search
echo "3. Query: 'revenue in 2023'"
curl -s -X POST "${BASE_URL}/query" \
    -H "Content-Type: application/json" \
    -d '{
        "q": "revenue in 2023",
        "top_k": 3
    }' | jq '.'
echo -e "\n"

# Test 4: Query - Another topic
echo "4. Query: 'main objectives'"
curl -s -X POST "${BASE_URL}/query" \
    -H "Content-Type: application/json" \
    -d '{
        "q": "main objectives",
        "top_k": 5
    }' | jq '.'
echo -e "\n"

# Test 5: Query with file type filter
echo "5. Query with PDF filter"
curl -s -X POST "${BASE_URL}/query" \
    -H "Content-Type: application/json" \
    -d '{
        "q": "document",
        "top_k": 3,
        "file_type": "pdf"
    }' | jq '.'
echo -e "\n"

# Test 6: Get specific document details (requires document_id from list)
echo "6. Get first document details"
DOC_ID=$(curl -s "${BASE_URL}/documents" | jq -r '.documents[0].document_id')
if [ "$DOC_ID" != "null" ] && [ -n "$DOC_ID" ]; then
    curl -s "${BASE_URL}/documents/${DOC_ID}" | jq '.document, .num_chunks'
else
    echo "No documents found"
fi
echo -e "\n"

echo "================================"
echo "Query tests completed!"
echo "================================"