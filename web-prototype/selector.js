window.onload = function () {
    if (window.opener === null) {
        document.write("ERROR - page open did not originate from authorized source");
        return;
    }

    $("div").arborFileManager({
        onPreview: function (project, datatype, dataset) {
            console.log("Preview button: (" + project + ", " + datatype + ", " + dataset + ")");
        },

        onSelect: function (project, datatype, dataset) {
            var data;

            console.log("Select button: (" + project + ", " + datatype + ", " + dataset + ")");
/*            window.opener.selected = {*/
                //project: project,
                //datatype: datatype,
                //dataset: dataset
            /*};*/
            data = {
                project: project,
                datatype: datatype,
                dataset: dataset
            };
            window.opener.postMessage(data, window.location.origin);
            window.close();
        }
    });
};
