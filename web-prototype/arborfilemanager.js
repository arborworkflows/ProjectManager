function error_message(msg) {
    d3.select(document.body)
        .append("h1")
        .style("color", "red")
        .text(msg);
}

function servicePath(){
    var pathArgs = Array.slice(arguments).join("/");
    if (pathArgs.length > 0) {
        pathArgs = "/" + pathArgs;
    }

    return "../tangelo/projmgr" + pathArgs;
}

window.onload = function () {
    "use strict";

    var hl_proj = null,
        hl_type = null,
        hl_dataset = null;

    function populate(projects){
        var ajax,
            items;

        ajax = d3.json(servicePath("project"));
        ajax.send("GET", function (err, projects) {
            if (err) {
                error_message("Could not connect to database");
                return;
            }

        items = d3.select("#projects")
            .selectAll("div")
            .data(projects, function (d) {
                return d;
            });
        items.enter()
            .append("div")
            .classed("item", true)
            .on("click", function (d) {
                var ajax,
                    delbutton;

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
                if (hl_proj && hl_proj.node() === this) {
                    return;
                }

                // Move the highlight to the selected project.
                if (hl_proj) {
                    hl_proj.classed("selected", false);
                }
                hl_proj = d3.select(this);
                hl_proj.classed("selected", true);

                delbutton = d3.select(this)
                    .select("a.btn")
                    .attr("disabled", true);
                delbutton.text("...");
                delbutton.transition()
                    .delay(1000)
                    .text("..");
                delbutton.transition()
                    .delay(2000)
                    .text(".");
                delbutton.transition()
                    .delay(3000)
                    .text("delete")
                    .attr("disabled", null);

                ajax = d3.json(servicePath("project", d));
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
                        .on("click", function (d) {
                            var ajax;

                            // If the click was on the highlighted item, bail
                            // (but, see TODO above).
                            if (hl_type && hl_type.node() === this) {
                                return;
                            }

                            // Move the highlight.
                            if (hl_type) {
                                hl_type.classed("selected", false);
                            }
                            hl_type = d3.select(this);
                            hl_type.classed("selected", true);

                            ajax = d3.json(servicePath("project", hl_proj.attr("name"), d));
                            ajax.send("GET", function (err, datasets) {
                                var dsets;

                                if (err) {
                                    error_message("Could not connect to database");
                                    return;
                                }

                                d3.select("#datasets")
                                    .selectAll("div")
                                    .remove();

                                dsets = d3.select("#datasets")
                                    .selectAll("div")
                                    .data(datasets)
                                    .enter()
                                    .append("div")
                                    .classed("item", true)
                                    .on("click", function (d) {
                                        // If the click was on the highlighted
                                        // item, bail (the TODO above doesn't
                                        // apply in this case).
                                        if (hl_dataset && hl_dataset.node() === this) {
                                            return;
                                        }

                                        // Move the highlight.
                                        if (hl_dataset) {
                                            hl_dataset.classed("selected", false);
                                        }
                                        hl_dataset = d3.select(this);
                                        hl_dataset.classed("selected", true);
                                    })
                                    .attr("name", function (d) {
                                        return d;
                                    })
                                    .html(function (d) {
                                        return d;
                                    });

                                    dsets.append("a")
                                        .classed("btn", true)
                                        .classed("btn-mini", true)
                                        .text("preview");

                                    dsets.append("a")
                                        .classed("btn", true)
                                        .classed("btn-mini", true)
                                        .text("select");

                                    dsets.append("a")
                                        .classed("btn", true)
                                        .classed("btn-mini", true)
                                        .text("delete")
                                        .on("click", function () {
                                            var ajax;

                                            ajax = d3.xhr(servicePath("project", hl_proj.attr("name"), hl_type.attr("name"), hl_dataset.attr("name")));
                                            ajax.send("DELETE", function (e, r) {
                                                if (e) {
                                                    console.log(e);
                                                    return;
                                                }

                                                console.log(r);
                                            });
                                        });
                            });
                        })
                        .attr("name", function (d) {
                            return d;
                        })
                        .text(function (d) {
                            return d;
                        });
                });

            })
            .attr("name", function (d) {
                return d;
            })
            .text(function (d) {
                return d;
            })
            .append("a")
            .classed("btn", true)
            .classed("btn-mini", true)
            .on("click", function () {
                var ajax,
                    name;

                name = d3.select(this.parentNode).attr("name");
                console.log(name);

                ajax = d3.xhr(servicePath("project", name));
                ajax.send("DELETE", function (e, r) {
                    if (e) {
                        console.log(e);
                        return;
                    }

                    populate();
                });
            });

            items.exit()
                .transition()
                .duration(1000)
                .style("height", "0px")
                .style("opacity", 0.0)
                .remove();
        });
    }

    d3.select("#newproject-ok")
        .on("click", function () {
            var name,
                ajax;

            name = encodeURI(d3.select("#newproject-name").property("value"));

            if (name !== "") {
                ajax = d3.xhr(servicePath("project", name));
                ajax.send("PUT", function (err, response) {
                    if (err) {
                        console.log("error: ");
                        console.log(err);
                        return;
                    }

                    populate();
                });
            }
        });

    populate();
};
