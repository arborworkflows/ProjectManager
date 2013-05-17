function error_message(msg) {
    d3.select(document.body)
        .append("h1")
        .style("color", "red")
        .text(msg);
}

window.onload = function () {
    "use strict";

    var ajax,
        hl = null;

    ajax = d3.json("../tangelo/projmgr/project");
    ajax.send("GET", function (err, projects) {
        if (err) {
            error_message("Could not connect to database");
            return;
        }

        d3.select("#projects")
            .selectAll("div")
            .data(projects)
            .enter()
            .append("div")
            .classed("project", true)
            .append("a")
            .on("click", function (d) {
                var ajax;

                // Move the highlight to the selected project.
                if (hl) {
                    hl.classed("selected", false);
                }
                hl = d3.select(this.parentNode);
                hl.classed("selected", true);

                ajax = d3.json("../tangelo/projmgr/project/" + d + "?q=types");
                ajax.send("GET", function (err, types) {
                    if (err) {
                        console.log(err);
                        error_message("Could not connect to database");
                        return;
                    }

                    console.log(types);

                    d3.select("#datatypes")
                        .selectAll("div")
                        .remove();

                    d3.select("#datatypes")
                        .selectAll("div")
                        .data(types)
                        .enter()
                        .append("div")
                        .text(function (d) {
                            return d;
                        });
                });

            })
            .attr("href", "#")
            .text(function (d) {
                return d;
            });
    });
};
