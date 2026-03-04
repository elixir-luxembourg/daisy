#!/bin/bash

# Script to update Solr schema for compatibility with Solr 9
# This script addresses known issues with django-haystack and Solr 9

set -e  # Exit on any error

SCHEMA_FILE="docker/solr/schema.xml"

echo "=== Solr Schema Update Script ==="

# Generate new schema using Django management command
echo "Step 1: Generating new schema using Django..."
echo "Running: python manage.py build_solr_schema -f $SCHEMA_FILE"
if ! python manage.py build_solr_schema -f "$SCHEMA_FILE"; then
    echo "❌ Error: Failed to generate schema using Django management command"
    exit 1
fi
echo "✅ Schema generated successfully"

# Change LatLonType to LatLonPointSpatialField
echo "Step 2: Updating location field type..."
if grep -q 'name="location".*class="solr.LatLonType"' "$SCHEMA_FILE"; then
    sed -i.bak 's/<fieldType name="location" class="solr.LatLonType" subFieldSuffix="_coordinate"\/>/<fieldType name="location" class="solr.LatLonPointSpatialField"\/>/' "$SCHEMA_FILE"
    echo "✅ Updated location fieldType from LatLonType to LatLonPointSpatialField"
fi

# Clean up backup file
if [ -f "$SCHEMA_FILE.bak" ]; then
    rm "$SCHEMA_FILE.bak"
fi
echo "=== Schema Update Complete ==="
echo "Updated schema file: $SCHEMA_FILE"
