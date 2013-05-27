window.onload = function () {
    d3.select("#select-link")
        .on("click", function () {
            window.open(window.location.origin + window.location.pathname.split("/").slice(0,-1).join("/") + "/selector.html", "_blank");
        });

    window.addEventListener("message", function (e) {
        d3.select("#report")
            .html("You selected: project <b>" + e.data.project + "</b>, data type <b>" + e.data.datatype + "</b>, dataset <b>" + e.data.dataset + "</b>.");
    });
};
