window.onload = function () {
    "use strict";

    var ajax;

    ajax = d3.json("../tangelo/projmgr/project");
    ajax.send("GET", function (err, projects) {
        if (err) {
            d3.select(document.body)
                .append("h1")
                .style("color", "red")
                .text("Could not connect to database");
            return;
        }

        d3.select("#projects")
            .selectAll("div")
            .data(projects)
            .enter()
            .append("div")
            .append("a")
            .attr("href", "#")
            .text(function (d) {
                return d;
            });
    });
};
