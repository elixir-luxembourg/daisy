FROM solr:7.3
RUN mkdir -p /opt/solr/server/solr/daisy/ \
    && cp -r /opt/solr/example/files/* /opt/solr/server/solr/daisy/. \
    && touch /opt/solr/server/solr/daisy/core.properties \
    &&  mkdir -p /opt/solr/server/solr/daisy_test/ \
    && cp -r /opt/solr/example/files/* /opt/solr/server/solr/daisy_test/. \
    && touch /opt/solr/server/solr/daisy_test/core.properties
COPY *.xml /opt/solr/server/solr/daisy/conf/
COPY *.xml /opt/solr/server/solr/daisy_test/conf/