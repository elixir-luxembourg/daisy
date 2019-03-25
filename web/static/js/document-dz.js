function loadDropzone(options){

/**
 * Load a dropzone element
 * files: list of files to display
 * config: dropzone configuration: http://www.dropzonejs.com/#configuration-options
 * selector: dropzone container selector
 * download_url: download url to attach to the element
 * delete_url: onclick deletable event
 */
    options.config['previewTemplate'] = document.querySelector('#dropzone-template').innerHTML

    Dropzone.autoDiscover = false;
    // hook plugin has it does not want <li> but takes div by default.
        // Dropzone.createElement = function(string) {
        // 	var el = $(string);
        // 	return el[0];
        // };

        var myDropzone = new Dropzone(options.selector, options.config);

        myDropzone.on("success", function(file, response) {
            // add download link
            var link = file.previewElement.getElementsByClassName('dlink')[0];
            // get file id
            var fileId = file.id
            if (typeof fileId == 'undefined') {
                fileId = response.id;
            }
            link.href =	options.download_url.replace(0, fileId);
            // add data url for deletable object
            file.previewElement.dataset.url = options.delete_url.replace(0, fileId);

            let editdoc = file.previewElement.getElementsByClassName('jsBtn')[0];

             editdoc.setAttribute('data-ajax-url', options.document_edit.replace(0, fileId));
        });

        for (var i = 0; i < options.files.length; i++) {
            myDropzone.emit("addedfile", options.files[i]);
            myDropzone.emit("success", options.files[i]);

        }
}