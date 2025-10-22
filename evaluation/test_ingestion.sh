#!/bin/bash

# Test ingestion service
echo "================================"
echo "Testing Document Ingestion"
echo "================================"
echo ""

BASE_URL="http://localhost:8000"

# Test 1: Health check
echo "1. Health Check"
curl -s "${BASE_URL}/health" | jq '.'
echo -e "\n"

# Test 2: Upload PDF
echo "2. Uploading sample PDF..."
if [ -f "../samples/sample1.pdf" ]; then
    RESPONSE=$(curl -s -X POST "${BASE_URL}/ingest" \
        -F "file=@../samples/sample1.pdf")
    echo $RESPONSE | jq '.'
    DOC_ID=$(echo $RESPONSE | jq -r '.document_id')
    echo "Document ID: $DOC_ID"
else
    echo "Error: sample1.pdf not found"
fi
echo -e "\n"

# Test 3: Upload DOCX
echo "3. Uploading sample DOCX..."
if [ -f "../samples/sample2.docx" ]; then
    RESPONSE=$(curl -s -X POST "${BASE_URL}/ingest" \
        -F "file=@../samples/sample2.docx")
    echo $RESPONSE | jq '.'
else
    echo "Error: sample2.docx not found"
fi
echo -e "\n"

# Test 4: Try invalid file type
echo "4. Testing invalid file type (should fail)..."
echo "test content" > /tmp/test.txt
curl -s -X POST "${BASE_URL}/ingest" \
    -F "file=@/tmp/test.txt" | jq '.'
rm /tmp/test.txt
echo -e "\n"

echo "================================"
echo "Ingestion tests completed!"
echo "Wait a few seconds for processing to complete, then run test_queries.sh"
echo "================================"