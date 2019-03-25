FROM node:11.10.1-stretch
COPY web/static/css /static/css
COPY web/static/js /static/js
COPY web/static/vendor/bootstrap-material-datetimepicker /static/vendor/bootstrap-material-datetimepicker
COPY web/static/vendor/package.json /static/vendor/package.json
WORKDIR /static/vendor/
RUN npm install
RUN npm run-script build
