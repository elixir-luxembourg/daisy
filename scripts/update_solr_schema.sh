#!/bin/bash

# Script to update Solr schema for compatibility with Solr 9
# This script addresses known issues with django-haystack and Solr 9

set -e  # Exit on any error

SCHEMA_FILE="docker/solr/schema.xml"

echo "=== Solr Schema Update Script ==="

# Step 0: Check if schema.xml exists
echo "Step 0: Checking if schema.xml exists..."
if [ ! -f "$SCHEMA_FILE" ]; then
    echo "❌ Error: $SCHEMA_FILE not found!"
    echo "Please make sure you're running this script from the project root directory."
    exit 1
fi

echo "✅ Found existing $SCHEMA_FILE"

# Step 1: Generate new schema using Django management command
echo "Step 1: Generating new schema using Django..."
echo "Running: python manage.py build_solr_schema -f $SCHEMA_FILE"

if ! python manage.py build_solr_schema -f "$SCHEMA_FILE"; then
    echo "❌ Error: Failed to generate schema using Django management command"
    exit 1
fi

echo "✅ Schema generated successfully"

# Step 2.1: Change LatLonType to LatLonPointSpatialField
echo "Step 2.1: Updating location field type..."
if grep -q 'name="location".*class="solr.LatLonType"' "$SCHEMA_FILE"; then
    sed -i.bak 's/<fieldType name="location" class="solr.LatLonType" subFieldSuffix="_coordinate"\/>/<fieldType name="location" class="solr.LatLonPointSpatialField"\/>/' "$SCHEMA_FILE"
    echo "✅ Updated location fieldType from LatLonType to LatLonPointSpatialField"
fi

# Step 2.2: Remove currency related fields
echo "Step 2.2: Removing currency-related fields..."

# Remove dynamicField for currency
if grep -q 'name="\*_c".*type="currency"' "$SCHEMA_FILE"; then
    sed -i.bak '/<dynamicField name="\*_c".*type="currency".*\/>/d' "$SCHEMA_FILE"
    echo "✅ Removed currency dynamicField"
fi

# Remove fieldType for currency
if grep -q 'name="currency".*class="solr.CurrencyField"' "$SCHEMA_FILE"; then
    sed -i.bak '/<fieldType name="currency" class="solr.CurrencyField".*\/>/d' "$SCHEMA_FILE"
    echo "✅ Removed currency fieldType"
fi

# Clean up backup file
if [ -f "$SCHEMA_FILE.bak" ]; then
    rm "$SCHEMA_FILE.bak"
fi

echo "=== Schema Update Complete ==="
echo "Updated schema file: $SCHEMA_FILE"
