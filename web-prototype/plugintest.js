window.onload = function () {
    $("div").arborFileManager({
        onPreview: function (project, datatype, dataset) {
            console.log("Preview button: (" + project + ", " + datatype + ", " + dataset + ")");
        },

        onSelect: function (project, datatype, dataset) {
            console.log("Select button: (" + project + ", " + datatype + ", " + dataset + ")");
        }
    });
};
