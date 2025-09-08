FROM solr:9.9-slim

USER root

# Create core directories with proper structure
RUN mkdir -p /var/solr/data/daisy/conf \
    && mkdir -p /var/solr/data/daisy/data \
    && mkdir -p /var/solr/data/daisy_test/conf \
    && mkdir -p /var/solr/data/daisy_test/data

# Copy default configuration files from Solr 9 template
RUN cp -r /opt/solr/server/solr/configsets/_default/conf/* /var/solr/data/daisy/conf/ \
    && cp -r /opt/solr/server/solr/configsets/_default/conf/* /var/solr/data/daisy_test/conf/

# Create core.properties files for both cores
RUN echo "name=daisy" > /var/solr/data/daisy/core.properties \
    && echo "name=daisy_test" > /var/solr/data/daisy_test/core.properties

# Copy your existing files to both cores
COPY *.xml /var/solr/data/daisy/conf/
COPY *.xml /var/solr/data/daisy_test/conf/

# Set proper ownership and permissions
RUN chown -R solr:solr /var/solr/data \
    && chmod -R 755 /var/solr/data

# Switch back to solr user
USER solr

# Expose Solr port
EXPOSE 8983