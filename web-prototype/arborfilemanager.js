function error_message(msg) {
    d3.select(document.body)
        .append("h1")
        .style("color", "red")
        .text(msg);
}

window.onload = function () {
    "use strict";

    var ajax,
        hl_proj = null,
        hl_type = null,
        hl_dataset = null;

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
            .classed("item", true)
            .append("a")
            .attr("href", "#")
            .text(function (d) {
                return d;
            })
            .on("click", function (d) {
                var ajax;

                // If the click was on the highlighted item, bail.
                //
                // TODO(choudhury): really instead of bailing, this action
                // should cause the page to *reload* all the information (in
                // case it has been asynchronously changed by some other
                // process).  In that case, we want to set a flag saying this is
                // what we're doing, which would cause us to remember to keep
                // any selected flag on the types, then initiate a click event
                // on the selected type, then "cascade" this same process onto
                // the datasets.
                if (hl_proj && hl_proj.node() === this.parentNode) {
                    return;
                }

                // Move the highlight to the selected project.
                if (hl_proj) {
                    hl_proj.classed("selected", false);
                }
                hl_proj = d3.select(this.parentNode);
                hl_proj.classed("selected", true);

                ajax = d3.json("../tangelo/projmgr/project/" + d);
                ajax.send("GET", function (err, types) {
                    if (err) {
                        console.log(err);
                        error_message("Could not connect to database");
                        return;
                    }

                    d3.select("#datatypes")
                        .selectAll("div")
                        .remove();

                    d3.select("#datasets")
                        .selectAll("div")
                        .remove();

                    d3.select("#datatypes")
                        .selectAll("div")
                        .data(types)
                        .enter()
                        .append("div")
                        .classed("item", true)
                        .append("a")
                        .attr("href", "#")
                        .text(function (d) {
                            return d;
                        })
                        .on("click", function (d) {
                            var ajax;

                            // If the click was on the highlighted item, bail
                            // (but, see TODO above).
                            if (hl_type && hl_type.node() === this.parentNode) {
                                return;
                            }

                            // Move the highlight.
                            if (hl_type) {
                                hl_type.classed("selected", false);
                            }
                            hl_type = d3.select(this.parentNode);
                            hl_type.classed("selected", true);

                            ajax = d3.json("../tangelo/projmgr/project/" + hl_proj.select("a").text() + "/" + d);
                            ajax.send("GET", function (err, datasets) {
                                if (err) {
                                    error_message("Could not connect to database");
                                    return;
                                }

                                d3.select("#datasets")
                                    .selectAll("div")
                                    .remove();

                                d3.select("#datasets")
                                    .selectAll("div")
                                    .data(datasets)
                                    .enter()
                                    .append("div")
                                    .classed("item", true)
                                    .append("a")
                                    .attr("href", "#")
                                    .text(function (d) {
                                        return d;
                                    })
                                    .on("click", function (d) {
                                        // If the click was on the highlighted
                                        // item, bail (the TODO above doesn't
                                        // apply in this case).
                                        if (hl_dataset && hl_dataset.node() === this.parentNode) {
                                            return;
                                        }

                                        // Move the highlight.
                                        if (hl_dataset) {
                                            hl_dataset.classed("selected", false);
                                        }
                                        hl_dataset = d3.select(this.parentNode);
                                        hl_dataset.classed("selected", false);
                                    });
                            });
                        });
                });

            });
    });
};
